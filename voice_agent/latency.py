"""Konuşma pipeline'ındaki (STT/EOU/LLM/TTS) gecikmeleri loglar.

`AgentSession`in yerleşik `metrics_collected` event'ini dinler; her odanın (konuşmanın)
metriklerini kendi dosyasına (`logs/<room>.jsonl`) tek satırlık JSON olarak yazar ve
aynı `speech_id`ye ait EOU + LLM + TTS metriklerini birleştirip "kullanıcı konuşmayı
bitirdi -> ajan sesle yanıt vermeye başladı" toplam gecikmesini de ayrıca loglar.

`model_name`/`model_provider` (Azure deployment adı vb. altyapı bilgisi) loglara
yazılmaz.

Analiz için: `scripts/latency_report.py`.
"""

from __future__ import annotations

import json
import logging
import re
from logging.handlers import RotatingFileHandler

from livekit.agents import AgentSession, metrics
from livekit.agents.voice.events import MetricsCollectedEvent

from . import config

logger = logging.getLogger(__name__)

_LOG_DIR = config.BASE_DIR / "logs"

_jsonl_loggers: dict[str, logging.Logger] = {}


def _sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") or "unknown"


def _get_jsonl_logger(room_name: str) -> logging.Logger:
    """Odaya özel, `logs/<room>.jsonl` dosyasına yazan logger'ı döner (ilk çağrıda kurar)."""
    safe_name = _sanitize_filename(room_name)
    logger_name = f"voice_agent.latency.jsonl.{safe_name}"
    if logger_name in _jsonl_loggers:
        return _jsonl_loggers[logger_name]

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_logger = logging.getLogger(logger_name)
    jsonl_logger.propagate = False
    jsonl_logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        _LOG_DIR / f"{safe_name}.jsonl", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    jsonl_logger.addHandler(handler)

    _jsonl_loggers[logger_name] = jsonl_logger
    return jsonl_logger


def attach_latency_logging(session: AgentSession, room_name: str) -> None:
    """Bir `AgentSession`a gecikme loglamasını bağlar. `session.start()`tan önce/sonra çağrılabilir."""
    jsonl_logger = _get_jsonl_logger(room_name)

    def _write_jsonl(record: dict) -> None:
        jsonl_logger.info(json.dumps(record, ensure_ascii=False))

    # speech_id -> o turdan toplanan EOU/LLM/TTS metrikleri
    turns: dict[str, dict] = {}

    def _on_metrics_collected(ev: MetricsCollectedEvent) -> None:
        m = ev.metrics
        # metadata (model_name/model_provider -> Azure deployment adı vb.) loglara sızmasın
        record = {"room": room_name, **m.model_dump(mode="json", exclude_none=True, exclude={"metadata"})}
        _write_jsonl(record)

        if isinstance(m, metrics.STTMetrics):
            logger.info(
                "STT: duration=%.3fs audio_duration=%.3fs (room=%s)",
                m.duration,
                m.audio_duration,
                room_name,
            )
        elif isinstance(m, metrics.EOUMetrics):
            logger.info(
                "EOU: end_of_utterance_delay=%.3fs transcription_delay=%.3fs (room=%s, speech_id=%s)",
                m.end_of_utterance_delay,
                m.transcription_delay,
                room_name,
                m.speech_id,
            )
            if m.speech_id:
                turns.setdefault(m.speech_id, {})["eou"] = m
        elif isinstance(m, metrics.LLMMetrics):
            logger.info(
                "LLM: ttft=%.3fs duration=%.3fs tokens_per_second=%.1f (room=%s, speech_id=%s)",
                m.ttft,
                m.duration,
                m.tokens_per_second,
                room_name,
                m.speech_id,
            )
            if m.speech_id:
                turns.setdefault(m.speech_id, {})["llm"] = m
        elif isinstance(m, metrics.TTSMetrics):
            logger.info(
                "TTS: ttfb=%.3fs duration=%.3fs (room=%s, speech_id=%s)",
                m.ttfb,
                m.duration,
                room_name,
                m.speech_id,
            )
            if m.speech_id:
                turn = turns.pop(m.speech_id, None)
                _maybe_log_turn_latency(room_name, m.speech_id, turn, m, _write_jsonl)

    session.on("metrics_collected", _on_metrics_collected)


def _maybe_log_turn_latency(
    room_name: str,
    speech_id: str,
    turn: dict | None,
    tts: "metrics.TTSMetrics",
    write_jsonl,
) -> None:
    """EOU + LLM + TTS metrikleri aynı tur için toplandıysa, uçtan uca (kullanıcı
    konuşmayı bitirdi -> ilk ses baytı) toplam algılanan gecikmeyi loglar."""
    if not turn or "eou" not in turn or "llm" not in turn:
        return

    eou: metrics.EOUMetrics = turn["eou"]
    llm: metrics.LLMMetrics = turn["llm"]

    total_delay = eou.end_of_utterance_delay + eou.transcription_delay + llm.ttft + tts.ttfb

    record = {
        "type": "turn_latency",
        "room": room_name,
        "speech_id": speech_id,
        "end_of_utterance_delay": eou.end_of_utterance_delay,
        "transcription_delay": eou.transcription_delay,
        "llm_ttft": llm.ttft,
        "tts_ttfb": tts.ttfb,
        "total_delay": total_delay,
    }
    write_jsonl(record)
    logger.info(
        "Tur gecikmesi (konuşma bitişi -> ilk ses): %.3fs (room=%s, speech_id=%s)",
        total_delay,
        room_name,
        speech_id,
    )
