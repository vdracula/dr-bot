# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

DB_PATH = os.getenv("DB_PATH", "birthdays.db")

RUS_CALENDAR_BASE = os.getenv(
    "RUS_CALENDAR_BASE",
    "https://russian-calendar.example.com/api",
)

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_ENDPOINT = os.getenv(
    "YANDEX_ENDPOINT",
    "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
)
YANDEX_MODEL = os.getenv(
    "YANDEX_MODEL",
    f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite" if YANDEX_FOLDER_ID else None,
)

DEFAULT_JOB_HOUR = int(os.getenv("JOB_HOUR", "9"))
DEFAULT_JOB_MINUTE = int(os.getenv("JOB_MINUTE", "0"))
