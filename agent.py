import logging

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
    room_io,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from voice_agent import config
from voice_agent.models import llm_model, stt_model, tts_model
from voice_agent.recording import maybe_start_recording, save_conversation, wait_and_report_recording
from voice_agent.tools import make_maths, web_search

logger = logging.getLogger(__name__)


class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=config.SYSTEM_PROMPT)

    async def on_enter(self) -> None:
        # when the agent is added to the session, it'll generate a reply
        # according to its instructions
        self.session.generate_reply(instructions=config.SYSTEM_PROMPT)


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    # each log entry will include these fields
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=stt_model,
        llm=llm_model,
        tts=tts_model,
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        tools=[make_maths, web_search],
    )

    recording_state: dict[str, str | None] = {"egress_id": None}

    async def log_usage() -> None:
        logger.info(f"Usage: {session.usage}")

    async def persist_conversation() -> None:
        await save_conversation(ctx.room.name, session)

    async def persist_recording() -> None:
        if egress_id := recording_state["egress_id"]:
            await wait_and_report_recording(ctx.room.name, egress_id)

    # shutdown callback'leri paralel çalışır (asyncio.gather); persist_recording'in
    # ~20-30 sn sürmesi persist_conversation'ı (transkript kaydını) geciktirmez.
    ctx.add_shutdown_callback(log_usage)
    ctx.add_shutdown_callback(persist_conversation)
    ctx.add_shutdown_callback(persist_recording)

    def on_participant_left(_participant) -> None:
        # LiveKit'in yerleşik close_on_disconnect'i sadece "temiz" disconnect
        # sebeplerini (örn. room.disconnect() çağrısı) kapsıyor; sekme kapatma veya
        # ağ kopması gibi durumlarda iş hiç sonlanmayabiliyor. Odada katılımcı
        # kalmadığında işi biz doğrudan sonlandırıyoruz ki transkript/kayıt kaydı
        # her durumda çalışsın.
        if len(ctx.room.remote_participants) == 0:
            logger.info("Katılımcı ayrıldı, oda boş; iş sonlandırılıyor (room=%s)", ctx.room.name)
            ctx.shutdown(reason="caller disconnected")

    ctx.room.on("participant_disconnected", on_participant_left)

    await session.start(
        agent=MyAgent(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(noise_cancellation=noise_cancellation.BVC()),
        ),
    )

    recording_info = await maybe_start_recording(ctx)
    if recording_info:
        recording_state["egress_id"] = recording_info.egress_id


if __name__ == "__main__":
    cli.run_app(server)
