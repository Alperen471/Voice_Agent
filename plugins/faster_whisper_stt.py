from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Literal

import numpy as np
from faster_whisper import WhisperModel

from livekit.agents import (
    APIConnectOptions,
    stt,
    utils,
)

from livekit.agents.types import (
    NOT_GIVEN,
    NotGivenOr,
    TimedString,
)

__all__ = [
    "FasterWhisperSTT",
    "AlignedStreamAdapter",
]

logger = logging.getLogger(__name__)


ModelSize = Literal[
    "tiny",
    "tiny.en",
    "base",
    "base.en",
    "small",
    "small.en",
    "medium",
    "medium.en",
    "large-v2",
    "large-v3",
    "large-v3-turbo",
]

Device = Literal[
    "cuda",
    "cpu",
    "auto",
]

ComputeType = Literal[
    "float16",
    "float32",
    "int8",
    "int8_float16",
    "int8_float32",
]


class FasterWhisperSTT(stt.STT):
    """
    Local FasterWhisper STT for LiveKit.

    Features:
        - Local GPU/CPU transcription
        - Turkish language hint
        - Word-level timestamps
        - LiveKit aligned transcript support
        - Hallucination filtering
        - Async-safe inference via asyncio.to_thread
    """

    def __init__(
        self,
        model_size: ModelSize = "large-v3-turbo",
        device: Device = "cuda",
        compute_type: ComputeType = "float16",
        language: str = "tr",
        beam_size: int = 1,
        vad_filter: bool = False,

        # Hallucination thresholds
        max_compression_ratio: float = 2.4,
        min_avg_logprob: float = -1.2,
        max_no_speech_prob: float = 0.6,
        min_word_probability: float = 0.15,
    ) -> None:

        super().__init__(
            capabilities=stt.STTCapabilities(
                streaming=False,
                interim_results=False,
                aligned_transcript="word",
            )
        )

        self._language = language
        self._beam_size = beam_size
        self._vad_filter = vad_filter

        self._max_compression_ratio = max_compression_ratio
        self._min_avg_logprob = min_avg_logprob
        self._max_no_speech_prob = max_no_speech_prob
        self._min_word_probability = min_word_probability

        logger.info(
            "Loading FasterWhisper model: %s on %s (%s)",
            model_size,
            device,
            compute_type,
        )

        self._model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )

        logger.info(
            (
                "FasterWhisper ready - "
                "language=%s "
                "beam_size=%s "
                "compression<=%.2f "
                "avg_logprob>=%.2f "
                "no_speech<=%.2f"
            ),
            language,
            beam_size,
            max_compression_ratio,
            min_avg_logprob,
            max_no_speech_prob,
        )

    # =========================================================
    # WHISPER INFERENCE
    # =========================================================

    def _transcribe_sync(
        self,
        audio_data: np.ndarray,
        language: str,
    ):
        segments, info = self._model.transcribe(
            audio_data,
            language=language,

            beam_size=self._beam_size,
            best_of=self._beam_size,

            temperature=0.0,

            vad_filter=self._vad_filter,

            word_timestamps=True,

            # FasterWhisper'ın kendi decoding guard'ları
            compression_ratio_threshold=self._max_compression_ratio,
            log_prob_threshold=self._min_avg_logprob,
            no_speech_threshold=self._max_no_speech_prob,

            # Uzun konuşmalarda önceki yanlış çıktının
            # bir sonraki segmenti bozmasını azaltır.
            condition_on_previous_text=False,
        )

        # FasterWhisper lazy generator döndürür.
        return list(segments), info

    # =========================================================
    # SIMPLE TEXT-LEVEL HALLUCINATION CHECK
    # =========================================================

    @staticmethod
    def _looks_like_repetition_hallucination(
        text: str,
    ) -> bool:

        text = text.strip()

        if not text:
            return False

        compact = re.sub(
            r"\s+",
            "",
            text,
        )

        # Örn:
        # ÖÖÖÖÖÖÖÖÖÖÖÖÖÖ
        if re.search(
            r"(.)\1{7,}",
            compact,
            flags=re.IGNORECASE,
        ):
            return True

        # Aynı kısa pattern'in defalarca tekrarı:
        # hahaha hahaha...
        if re.search(
            r"(.{1,4})\1{6,}",
            compact,
            flags=re.IGNORECASE,
        ):
            return True

        # Uzun bir text ama çok az unique karakter
        if len(compact) >= 20:

            unique_chars = set(
                compact.lower()
            )

            if len(unique_chars) <= 3:
                return True

        return False

    # =========================================================
    # SEGMENT QUALITY CHECK
    # =========================================================

    def _segment_is_valid(
        self,
        segment,
    ) -> bool:

        # -----------------------------------------------------
        # 1. no_speech_prob
        # -----------------------------------------------------

        if (
            segment.no_speech_prob is not None
            and segment.no_speech_prob
            > self._max_no_speech_prob
        ):
            logger.warning(
                (
                    "Dropping Whisper segment: "
                    "high no_speech_prob "
                    "text=%r "
                    "no_speech_prob=%.3f"
                ),
                segment.text,
                segment.no_speech_prob,
            )

            return False

        # -----------------------------------------------------
        # 2. avg_logprob
        # -----------------------------------------------------

        if (
            segment.avg_logprob is not None
            and segment.avg_logprob
            < self._min_avg_logprob
        ):
            logger.warning(
                (
                    "Dropping Whisper segment: "
                    "low avg_logprob "
                    "text=%r "
                    "avg_logprob=%.3f"
                ),
                segment.text,
                segment.avg_logprob,
            )

            return False

        # -----------------------------------------------------
        # 3. compression_ratio
        # -----------------------------------------------------

        if (
            segment.compression_ratio is not None
            and segment.compression_ratio
            > self._max_compression_ratio
        ):
            logger.warning(
                (
                    "Dropping Whisper segment: "
                    "high compression_ratio "
                    "text=%r "
                    "compression_ratio=%.3f"
                ),
                segment.text,
                segment.compression_ratio,
            )

            return False

        # -----------------------------------------------------
        # 4. obvious repetition hallucination
        # -----------------------------------------------------

        if self._looks_like_repetition_hallucination(
            segment.text
        ):
            logger.warning(
                (
                    "Dropping Whisper segment: "
                    "repetition hallucination "
                    "text=%r"
                ),
                segment.text,
            )

            return False

        return True

    # =========================================================
    # LIVEKIT RECOGNIZE
    # =========================================================

    async def _recognize_impl(
        self,
        buffer: utils.AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> stt.SpeechEvent:

        # =====================================================
        # 1. AudioBuffer -> numpy
        # =====================================================

        if isinstance(buffer, list):

            chunks: list[np.ndarray] = []

            for frame in buffer:

                frame_data = np.frombuffer(
                    frame.data,
                    dtype=np.int16,
                )

                chunks.append(
                    frame_data
                )

            if chunks:

                audio_data = (
                    np.concatenate(chunks)
                    .astype(np.float32)
                    / 32768.0
                )

            else:

                audio_data = np.array(
                    [],
                    dtype=np.float32,
                )

        else:

            audio_data = (
                np.frombuffer(
                    buffer.data,
                    dtype=np.int16,
                )
                .astype(np.float32)
                / 32768.0
            )

        # =====================================================
        # 2. Empty buffer guard
        # =====================================================

        if audio_data.size == 0:

            logger.debug(
                "Empty audio buffer received"
            )

            return self._empty_event(
                language=self._language,
            )

        # =====================================================
        # 3. Language
        # =====================================================

        lang = (
            language
            if language is not NOT_GIVEN
            else self._language
        )

        # =====================================================
        # 4. Inference
        # =====================================================

        started_at = (
            time.perf_counter()
        )

        segments, info = await asyncio.to_thread(
            self._transcribe_sync,
            audio_data,
            lang,
        )

        elapsed_ms = (
            time.perf_counter()
            - started_at
        ) * 1000

        # =====================================================
        # 5. Filter segments
        # =====================================================

        accepted_segments = []

        for segment in segments:

            logger.debug(
                (
                    "SEGMENT "
                    "text=%r "
                    "avg_logprob=%.3f "
                    "compression_ratio=%.3f "
                    "no_speech_prob=%.3f"
                ),
                segment.text,
                segment.avg_logprob,
                segment.compression_ratio,
                segment.no_speech_prob,
            )

            if not self._segment_is_valid(
                segment
            ):
                continue

            accepted_segments.append(
                segment
            )

        # =====================================================
        # 6. No valid transcription
        # =====================================================

        if not accepted_segments:

            logger.warning(
                (
                    "All Whisper segments were rejected "
                    "latency=%.0fms "
                    "audio=%.2fs"
                ),
                elapsed_ms,
                info.duration,
            )

            return self._empty_event(
                language=lang,
            )

        # =====================================================
        # 7. Build transcript
        # =====================================================

        text_parts: list[str] = []

        timed_words: list[
            TimedString
        ] = []

        for segment in accepted_segments:

            text_parts.append(
                segment.text
            )

            if not segment.words:
                continue

            for word in segment.words:

                # Word-level probability filtering.
                #
                # FasterWhisper word timestamps ile beraber
                # probability alanı da döndürür.
                probability = getattr(
                    word,
                    "probability",
                    None,
                )

                if (
                    probability is not None
                    and probability
                    < self._min_word_probability
                ):
                    logger.debug(
                        (
                            "Skipping low-confidence word "
                            "word=%r "
                            "probability=%.3f"
                        ),
                        word.word,
                        probability,
                    )

                    continue

                timed_words.append(
                    TimedString(
                        word.word,
                        start_time=word.start,
                        end_time=word.end,
                    )
                )

                logger.debug(
                    (
                        "WORD "
                        "text=%r "
                        "start=%.3f "
                        "end=%.3f "
                        "probability=%s"
                    ),
                    word.word,
                    word.start,
                    word.end,
                    (
                        f"{probability:.3f}"
                        if probability
                        is not None
                        else "unknown"
                    ),
                )

        text = "".join(
            text_parts
        ).strip()

        # =====================================================
        # 8. Final text hallucination guard
        # =====================================================

        if (
            not text
            or self._looks_like_repetition_hallucination(
                text
            )
        ):

            logger.warning(
                (
                    "Final Whisper transcript rejected "
                    "text=%r"
                ),
                text,
            )

            return self._empty_event(
                language=lang,
            )

        # =====================================================
        # 9. Timing
        # =====================================================

        if timed_words:

            first_word_start = (
                timed_words[0]
                .start_time
            )

            last_word_end = (
                timed_words[-1]
                .end_time
            )

        else:

            # Words filtrelenmiş olabilir.
            #
            # Segment timing'i fallback olarak kullan.
            first_word_start = (
                accepted_segments[0]
                .start
            )

            last_word_end = (
                accepted_segments[-1]
                .end
            )

        # =====================================================
        # 10. Log final result
        # =====================================================

        logger.info(
            (
                "STT accepted "
                "text=%r "
                "language=%s "
                "latency=%.0fms "
                "audio=%.2fs "
                "start=%.3f "
                "end=%.3f "
                "words=%d "
                "accepted_segments=%d/%d"
            ),
            text,
            info.language,
            elapsed_ms,
            info.duration,
            first_word_start,
            last_word_end,
            len(timed_words),
            len(accepted_segments),
            len(segments),
        )

        # =====================================================
        # 11. LiveKit SpeechEvent
        # =====================================================

        return stt.SpeechEvent(
            type=(
                stt.SpeechEventType
                .FINAL_TRANSCRIPT
            ),
            alternatives=[
                stt.SpeechData(
                    text=text,
                    language=lang or "",
                    start_time=first_word_start,
                    end_time=last_word_end,
                    words=timed_words,
                )
            ],
        )

    # =========================================================
    # EMPTY TRANSCRIPT
    # =========================================================

    @staticmethod
    def _empty_event(
        *,
        language: str,
    ) -> stt.SpeechEvent:

        return stt.SpeechEvent(
            type=(
                stt.SpeechEventType
                .FINAL_TRANSCRIPT
            ),
            alternatives=[
                stt.SpeechData(
                    text="",
                    language=language or "",
                    start_time=0.0,
                    end_time=0.0,
                    words=[],
                )
            ],
        )


class AlignedStreamAdapter(
    stt.StreamAdapter
):
    """
    LiveKit StreamAdapter that preserves
    aligned_transcript capability.

    FasterWhisper itself is batch STT.

    Silero VAD:
        audio stream
            ↓
        speech segment
            ↓
        FasterWhisper
            ↓
        FINAL_TRANSCRIPT + words

    This adapter exposes that pipeline as a LiveKit
    streaming STT interface while preserving word alignment.
    """

    def __init__(
        self,
        *,
        stt_model: stt.STT,
        vad,
    ) -> None:

        super().__init__(
            stt=stt_model,
            vad=vad,
        )

        self._capabilities.aligned_transcript = (
            stt_model
            .capabilities
            .aligned_transcript
        )

        logger.info(
            (
                "AlignedStreamAdapter ready - "
                "streaming=%s "
                "interim=%s "
                "aligned=%s"
            ),
            self.capabilities.streaming,
            self.capabilities.interim_results,
            self.capabilities.aligned_transcript,
        )