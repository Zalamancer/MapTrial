"""Earth Engine REST API authentication using a service account."""

import threading
import time

from google.auth.transport.requests import Request
from google.oauth2 import service_account

import config

_lock = threading.Lock()
_credentials = None


def _build_credentials():
    """Create scoped credentials from the service account JSON."""
    if not config.SERVICE_ACCOUNT_CREDENTIALS:
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS_JSON is not set or is empty."
        )
    creds = service_account.Credentials.from_service_account_info(
        config.SERVICE_ACCOUNT_CREDENTIALS,
        scopes=[config.EE_SCOPE, config.CLOUD_SCOPE],
    )
    return creds


def get_access_token() -> str:
    """Return a valid access token, refreshing if needed.

    Thread-safe: multiple Flask workers can call this concurrently.
    """
    global _credentials
    with _lock:
        if _credentials is None:
            _credentials = _build_credentials()
        if not _credentials.valid or (
            _credentials.expiry
            and _credentials.expiry.timestamp() - time.time() < 60
        ):
            _credentials.refresh(Request())
        return _credentials.token


def auth_headers() -> dict:
    """Return Authorization header dict for Earth Engine REST calls."""
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
    }
