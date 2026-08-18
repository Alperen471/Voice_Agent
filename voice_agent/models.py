import os

from livekit.agents import stt,llm,tts,inference
from livekit.plugins import openai,silero

from . import config  # noqa: F401  (.env dosyasını yükler)

vad = silero.VAD.load()

azure_stt = stt.StreamAdapter(
    stt=openai.STT.with_azure(
        model="gpt-4o-mini-transcribe",
        azure_deployment=os.getenv("STT_DEPLOYMENT_NAME"),
        language="tr"
    ),
    vad=vad
)

stt_model = stt.FallbackAdapter([
    azure_stt,
    inference.STT.from_model_string("deepgram/nova-3")
])


llm_model=llm.FallbackAdapter(
    [
        openai.LLM.with_azure(
        model="gpt-4o-mini",
        azure_deployment=os.getenv("LLM_DEPLOYMENT_NAME")
    ),
    inference.LLM("openai/gpt-4.1-mini")
    ]
)

tts_model=tts.FallbackAdapter([
    openai.TTS.with_azure(
        model="tts-1",
        azure_deployment=os.getenv("TTS_DEPLOYMENT_NAME"),
        voice="nova"
    ),
    inference.TTS.from_model_string(model="cartesia/sonic-3:0f95596c-09c4-4418-99fe-5c107e0713c0")
])
