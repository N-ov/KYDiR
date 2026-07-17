"""Настройки приложения. Всё переопределяется переменными окружения."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("KYDIR_DATA_DIR", BASE_DIR / "data"))
DB_PATH = Path(os.environ.get("KYDIR_DB", DATA_DIR / "kydir.db"))

SESSION_COOKIE = "kydir_session"
SESSION_TTL_DAYS = int(os.environ.get("KYDIR_SESSION_TTL_DAYS", "30"))
# На VPS за HTTPS выставить KYDIR_COOKIE_SECURE=1
COOKIE_SECURE = os.environ.get("KYDIR_COOKIE_SECURE", "0") == "1"

FRONTEND_DIR = BASE_DIR / "frontend"
