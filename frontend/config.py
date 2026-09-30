"""Frontend settings. Override any of these with environment variables."""
import os

APP_TITLE = "Industrial Crisis Command Center"
PLANT_NAME = "Riverside Chemical Complex"

# FastAPI backend
BASE_URL = os.getenv("CRISIS_API_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = float(os.getenv("CRISIS_API_TIMEOUT", "2"))

# When the backend is unreachable, use built-in mock data so the UI still works.
# Set CRISIS_ALLOW_MOCK=false for the final integrated demo.
ALLOW_MOCK_FALLBACK = os.getenv("CRISIS_ALLOW_MOCK", "true").lower() == "true"
RETRY_BACKEND_AFTER_SEC = 15  # after a connection failure, wait before retrying

REFRESH_SECONDS = 5
DEFAULT_INCIDENT_ID = "INC-001"

COLORS = {
    "bg": "#0E1821",
    "panel": "#16242F",
    "line": "#2A3B49",
    "text": "#D9E2EA",
    "muted": "#8A9BAA",
    "danger": "#E5484D",
    "warn": "#F2A900",   # safety yellow
    "ok": "#3DD68C",
    "info": "#4FA3E0",
}