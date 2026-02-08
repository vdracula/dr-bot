# Telegram бот «Праздники и дни рождения»

Бот для групп в Telegram, который:

- каждый день в заданное время пишет в чат список праздников на сегодня;
- поздравляет участников с днём рождения с помощью YandexGPT (весёлые тексты);
- хранит дни рождения в SQLite;
- поддерживает несколько чатов одновременно.

## Стек

- Python 3.10+
- [python-telegram-bot 21.x][web:62]
- SQLite (через стандартный модуль `sqlite3`)[web:79]
- YandexGPT Text Generation API[web:160][web:172]

## Установка

```bash
git clone <repo-url>
cd <repo-folder>
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
