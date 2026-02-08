# holidays.py
import os
from datetime import datetime
from config import RUS_CALENDAR_BASE

import requests

RUS_CALENDAR_BASE = os.getenv("RUS_CALENDAR_BASE", "https://russian-calendar.example.com/api")
HOLIDAYS_ENDPOINT = f"{RUS_CALENDAR_BASE}/holidays"


def get_today_holidays():
    """
    Russian Calendar API, фильтрация по сегодняшней дате.
    Ожидаемый формат:
    [
      {"date": "YYYY-MM-DD", "holidayName": "..."},
      ...
    ]
    [web:7][web:21]
    """
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        resp = requests.get(HOLIDAYS_ENDPOINT, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    holidays_today = [
        item["holidayName"]
        for item in data
        if item.get("date") == today and "holidayName" in item
    ]
    return holidays_today

