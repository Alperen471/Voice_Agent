import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SYSTEM_PROMPT = (BASE_DIR / "system_prompt.txt").read_text(encoding="utf-8")

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:5000")

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

RECORDING_S3_BUCKET = os.getenv("RECORDING_S3_BUCKET", "")
RECORDING_S3_REGION = os.getenv("RECORDING_S3_REGION", "")
RECORDING_S3_ACCESS_KEY = os.getenv("RECORDING_S3_ACCESS_KEY", "")
RECORDING_S3_SECRET_KEY = os.getenv("RECORDING_S3_SECRET_KEY", "")
RECORDING_S3_ENDPOINT = os.getenv("RECORDING_S3_ENDPOINT", "")

RECORDING_ENABLED = bool(
    RECORDING_S3_BUCKET and RECORDING_S3_REGION and RECORDING_S3_ACCESS_KEY and RECORDING_S3_SECRET_KEY
)
