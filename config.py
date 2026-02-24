"""Application configuration loaded from environment variables."""

import json
import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
APP_URL = os.environ.get("APP_URL", "http://localhost:8080")
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")

# Parse service account credentials from JSON string
_creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON", "")
SERVICE_ACCOUNT_CREDENTIALS = json.loads(_creds_json) if _creds_json else {}

EE_API_BASE = "https://earthengine.googleapis.com"
EE_SCOPE = "https://www.googleapis.com/auth/earthengine"
CLOUD_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
