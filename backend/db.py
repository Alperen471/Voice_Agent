from functools import lru_cache

from supabase import Client, create_client

import config

TABLE = "conversations"


@lru_cache
def get_client() -> Client:
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)


def init_db() -> None:
    """Tablo (conversations) ve recordings bucket'ı Supabase panelinde önceden oluşturulur."""


def create_conversation(conversation_id: str, started_at: str) -> None:
    get_client().table(TABLE).insert({"id": conversation_id, "status": "active", "started_at": started_at}).execute()


def complete_conversation(
    conversation_id: str,
    *,
    ended_at: str,
    status: str,
    transcript: dict | None,
    error_message: str | None,
) -> None:
    """Transkripti kaydeder. Kayıt (recording) durumu ayrı ve bağımsız olarak mark_recording_ready ile güncellenir."""
    update = {"status": status, "ended_at": ended_at, "error_message": error_message}
    if transcript is not None:
        update["transcript"] = transcript
    get_client().table(TABLE).update(update).eq("id", conversation_id).execute()


def mark_recording_ready(conversation_id: str) -> None:
    get_client().table(TABLE).update({"has_recording": True}).eq("id", conversation_id).execute()


def _recording_path(conversation_id: str) -> str:
    # agent.py egress dosyasını her zaman bu deterministik isimle yazıyor.
    return f"recordings/{conversation_id}.ogg"


def _build_recording_url(conversation_id: str) -> str:
    """recordings bucket'ındaki dosya için, okuma anında, herkese açık URL üretir (DB'de saklanmaz)."""
    return get_client().storage.from_(config.SUPABASE_RECORDINGS_BUCKET).get_public_url(_recording_path(conversation_id))


def _row_to_summary(row: dict) -> dict:
    transcript = row.get("transcript")
    return {
        "id": row["id"],
        "status": row["status"],
        "started_at": row["started_at"],
        "ended_at": row["ended_at"],
        "has_recording": bool(row.get("has_recording")),
        "turn_count": len(transcript["items"]) if transcript else 0,
    }


def _row_to_detail(row: dict) -> dict:
    return {
        "id": row["id"],
        "status": row["status"],
        "started_at": row["started_at"],
        "ended_at": row["ended_at"],
        "transcript": row.get("transcript"),
        "recording_url": _build_recording_url(row["id"]) if row.get("has_recording") else None,
        "error_message": row.get("error_message"),
    }


def list_conversations() -> list[dict]:
    res = get_client().table(TABLE).select("*").order("started_at", desc=True).execute()
    return [_row_to_summary(r) for r in res.data]


def get_conversation(conversation_id: str) -> dict | None:
    res = get_client().table(TABLE).select("*").eq("id", conversation_id).limit(1).execute()
    return _row_to_detail(res.data[0]) if res.data else None
