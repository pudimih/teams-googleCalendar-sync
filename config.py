import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env localizado na mesma pasta do projeto
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# ==========================================
# Microsoft Teams
# ==========================================
TEAMS_AUTH_TOKEN = os.getenv("TEAMS_AUTH_TOKEN", "").strip()

# ==========================================
# Google Calendar
# ==========================================
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary").strip()
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
GOOGLE_TOKEN_FILE = BASE_DIR / "token.json"
SYNCED_FILE = BASE_DIR / "synced_assignments.json"
