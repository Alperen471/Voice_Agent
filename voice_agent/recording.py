import asyncio
import logging

import httpx
from livekit import api as lk_api
from livekit.agents import AgentSession, JobContext

from . import config

logger = logging.getLogger(__name__)


async def save_conversation(room_name: str, session: AgentSession) -> None:
    """Frontend'in konuşma detay sayfasında gösterebilmesi için transkripti FastAPI backend'ine kaydeder.

    Kayıt (recording) durumunu beklemez — bu yüzden çağrıldığı an hemen tamamlanır.
    """
    transcript = session.history.to_dict(exclude_timestamp=False, exclude_function_call=True)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.patch(
                f"{config.BACKEND_API_URL}/api/conversations/{room_name}",
                json={"status": "completed", "transcript": transcript},
            )
            response.raise_for_status()
        logger.info("Konuşma transkripti backend'e kaydedildi (room=%s)", room_name)
    except Exception:
        logger.exception("Konuşma transkripti backend'e kaydedilemedi (room=%s)", room_name)


async def wait_and_report_recording(
    room_name: str, egress_id: str, *, timeout: float = 30.0, interval: float = 2.0
) -> None:
    """Egress'in bitmesini bekler ve SADECE tamamlanırsa backend'e ayrıca haber verir.

    save_conversation'dan bağımsız, ayrı bir shutdown callback olarak çalışır; bu yüzden
    transkript kaydını geciktirmez (LiveKit Agents shutdown callback'leri paralel çalıştırır).
    """
    lkapi = lk_api.LiveKitAPI(config.LIVEKIT_URL, config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET)
    completed = False
    try:
        elapsed = 0.0
        while elapsed < timeout:
            res = await lkapi.egress.list_egress(lk_api.ListEgressRequest(egress_id=egress_id))
            if res.items:
                status = res.items[0].status
                if status == lk_api.EGRESS_COMPLETE:
                    completed = True
                    break
                if status in (lk_api.EGRESS_FAILED, lk_api.EGRESS_ABORTED):
                    logger.warning(
                        "Ses kaydı tamamlanamadı (egress_id=%s, status=%s, error=%s)",
                        egress_id,
                        lk_api.EgressStatus.Name(status),
                        res.items[0].error,
                    )
                    return
            await asyncio.sleep(interval)
            elapsed += interval
    finally:
        await lkapi.aclose()

    if not completed:
        logger.warning("Ses kaydı durumu zaman aşımına uğradı (egress_id=%s)", egress_id)
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{config.BACKEND_API_URL}/api/conversations/{room_name}/recording-ready")
            response.raise_for_status()
        logger.info("Ses kaydı hazır olarak işaretlendi (room=%s, egress_id=%s)", room_name, egress_id)
    except Exception:
        logger.exception("Ses kaydı durumu backend'e bildirilemedi (room=%s, egress_id=%s)", room_name, egress_id)


async def maybe_start_recording(ctx: JobContext) -> lk_api.EgressInfo | None:
    """RECORDING_S3_* değişkenleri .env'de tanımlıysa oda sesini S3-uyumlu bucket'a kaydeder."""
    if not config.RECORDING_ENABLED:
        logger.info("Ses kaydı devre dışı: RECORDING_S3_* değişkenleri .env'de tanımlı değil.")
        return None

    lkapi = lk_api.LiveKitAPI(config.LIVEKIT_URL, config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET)
    try:
        request = lk_api.RoomCompositeEgressRequest(
            room_name=ctx.room.name,
            audio_only=True,
            file_outputs=[
                lk_api.EncodedFileOutput(
                    file_type=lk_api.EncodedFileType.OGG,
                    filepath=f"recordings/{ctx.room.name}.ogg",
                    s3=lk_api.S3Upload(
                        access_key=config.RECORDING_S3_ACCESS_KEY,
                        secret=config.RECORDING_S3_SECRET_KEY,
                        region=config.RECORDING_S3_REGION,
                        bucket=config.RECORDING_S3_BUCKET,
                        endpoint=config.RECORDING_S3_ENDPOINT or None,
                        # Supabase (ve çoğu S3-uyumlu servis) bucket'ı subdomain olarak değil,
                        # path içinde bekler; aksi halde TLS sertifika/handshake hatası alınır.
                        force_path_style=True,
                    ),
                )
            ],
        )
        info = await lkapi.egress.start_room_composite_egress(request)
        logger.info("Ses kaydı (egress) başlatıldı (room=%s, egress_id=%s)", ctx.room.name, info.egress_id)
        return info
    except Exception:
        logger.exception("Ses kaydı (egress) başlatılamadı (room=%s)", ctx.room.name)
        return None
    finally:
        await lkapi.aclose()
