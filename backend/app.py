import logging
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from livekit import api as lk_api
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

import config
import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(title="Sesli Asistan API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "bad_request"):
        self.message = message
        self.status_code = status_code
        self.code = code


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


@app.exception_handler(ApiError)
async def handle_api_error(_request: Request, err: ApiError):
    return error_response(err.status_code, err.code, err.message)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_request: Request, _err: RequestValidationError):
    return error_response(400, "invalid_body", "Geçersiz istek gövdesi.")


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(_request: Request, err: StarletteHTTPException):
    code = "not_found" if err.status_code == 404 else "http_error"
    return error_response(err.status_code, code, str(err.detail))


@app.exception_handler(Exception)
async def handle_unexpected(_request: Request, err: Exception):
    logger.exception("Unhandled error")
    return error_response(500, "internal_error", "Beklenmeyen bir sunucu hatası oluştu.")


class SystemPromptUpdate(BaseModel):
    content: str


class CompleteConversationRequest(BaseModel):
    status: Literal["completed", "failed"] = "completed"
    transcript: dict | None = None
    error_message: str | None = None


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/system-prompt")
def get_system_prompt():
    if not config.SYSTEM_PROMPT_PATH.exists():
        raise ApiError("Sistem promptu dosyası bulunamadı.", 404, "not_found")
    return {"content": config.SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")}


@app.put("/api/system-prompt")
def update_system_prompt(body: SystemPromptUpdate):
    if not body.content.strip():
        raise ApiError("Sistem promptu boş olamaz.", 400, "invalid_content")
    config.SYSTEM_PROMPT_PATH.write_text(body.content, encoding="utf-8")
    return {"content": body.content}


@app.post("/api/conversations", status_code=201)
def start_conversation():
    """Yeni bir LiveKit odası + erişim tokenı üretir; agent.py bu odaya otomatik katılır."""
    if not (config.LIVEKIT_URL and config.LIVEKIT_API_KEY and config.LIVEKIT_API_SECRET):
        raise ApiError(
            "LiveKit yapılandırması eksik. .env dosyasına LIVEKIT_URL, LIVEKIT_API_KEY ve "
            "LIVEKIT_API_SECRET değerlerini girin.",
            503,
            "livekit_not_configured",
        )

    conversation_id = uuid.uuid4().hex
    identity = f"caller-{uuid.uuid4().hex[:8]}"

    grants = lk_api.VideoGrants(room_join=True, room=conversation_id, can_publish=True, can_subscribe=True)
    token = (
        lk_api.AccessToken(config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(grants)
        .to_jwt()
    )

    db.create_conversation(conversation_id, started_at=datetime.now(timezone.utc).isoformat())

    return {
        "conversation_id": conversation_id,
        "room_name": conversation_id,
        "token": token,
        "url": config.LIVEKIT_URL,
    }


@app.patch("/api/conversations/{conversation_id}")
def complete_conversation(conversation_id: str, body: CompleteConversationRequest):
    """agent.py tarafından, oturum kapanır kapanmaz transkripti bildirmek için çağrılır (kayıt beklemez)."""
    if db.get_conversation(conversation_id) is None:
        raise ApiError("Konuşma bulunamadı.", 404, "not_found")

    db.complete_conversation(
        conversation_id,
        ended_at=datetime.now(timezone.utc).isoformat(),
        status=body.status,
        transcript=body.transcript,
        error_message=body.error_message,
    )
    return db.get_conversation(conversation_id)


@app.post("/api/conversations/{conversation_id}/recording-ready")
def mark_recording_ready(conversation_id: str):
    """agent.py, egress'in tamamlandığını kendisi doğruladıktan SONRA çağırır."""
    if db.get_conversation(conversation_id) is None:
        raise ApiError("Konuşma bulunamadı.", 404, "not_found")
    db.mark_recording_ready(conversation_id)
    return db.get_conversation(conversation_id)


@app.get("/api/conversations")
def list_conversations():
    return {"conversations": db.list_conversations()}


@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    convo = db.get_conversation(conversation_id)
    if convo is None:
        raise ApiError("Konuşma bulunamadı.", 404, "not_found")
    return convo
