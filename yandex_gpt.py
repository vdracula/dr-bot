# yandex_gpt.py
import os
import requests
from config import YANDEX_API_KEY, YANDEX_FOLDER_ID, YANDEX_ENDPOINT, YANDEX_MODEL

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_ENDPOINT = os.getenv(
    "YANDEX_ENDPOINT",
    "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
)
YANDEX_MODEL = os.getenv(
    "YANDEX_MODEL",
    f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
)


def generate_birthday_text(name_html: str) -> str:
    """
    Весёлое поздравление через YandexGPT, fallback — статичное.
    [web:160][web:170][web:172]
    """
    if not (YANDEX_API_KEY and YANDEX_FOLDER_ID):
        return (
            f"🎉 Сегодня день рождения у {name_html}! "
            f"Желаю здоровья, вдохновения и мощных результатов во всех проектах! 🥳"
        )

    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json",
        "x-folder-id": YANDEX_FOLDER_ID,
    }

    prompt = (
        "Сгенерируй короткое, весёлое поздравление с днём рождения на русском языке, "
        "на «ты», максимум 2 предложения. "
        f"Обращайся по имени: {name_html}."
    )

    body = {
        "modelUri": YANDEX_MODEL,
        "completionOptions": {
            "maxTokens": 120,
            "temperature": 0.8,
            "stream": False,
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты дружелюбный и остроумный человек, умеющий шутить без пошлости.",
            },
            {"role": "user", "text": prompt},
        ],
    }

    try:
        resp = requests.post(
            YANDEX_ENDPOINT, headers=headers, json=body, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        alt = data["result"]["alternatives"][0]
        text = alt["message"]["text"].strip()
        if "🎉" not in text and "🥳" not in text:
            text = "🎉 " + text
        return text
    except Exception:
        return (
            f"🎉 Сегодня день рождения у {name_html}! "
            f"Желаю здоровья, вдохновения и мощных результатов во всех проектах! 🥳"
        )
