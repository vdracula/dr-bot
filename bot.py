# bot.py
import logging
import os

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    JobQueue,
)

from db import init_db
from handlers import (
    start,
    add_chat_cmd,
    bday,
    list_my_bdays_cmd,
    del_my_bday_cmd,
    list_bdays_cmd,
    del_bday_cmd,
    enable_cmd,
    disable_cmd,
    time_cmd,
    scheduler_tick,
    debug_holidays_cmd,
    )
from config import BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def on_startup(app):
    job_queue: JobQueue = app.job_queue
    job_queue.run_repeating(
        scheduler_tick,
        interval=60,
        first=10,
        name="scheduler_tick",
    )
    logger.info("Scheduler job started (every 60s).")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN в переменных окружения.")

    init_db()

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(on_startup)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_chat_cmd))
    app.add_handler(CommandHandler("bday", bday))
    app.add_handler(CommandHandler("list_my_bdays", list_my_bdays_cmd))
    app.add_handler(CommandHandler("del_my_bday", del_my_bday_cmd))
    app.add_handler(CommandHandler("list_bdays", list_bdays_cmd))
    app.add_handler(CommandHandler("del_bday", del_bday_cmd))
    app.add_handler(CommandHandler("enable", enable_cmd))
    app.add_handler(CommandHandler("disable", disable_cmd))
    app.add_handler(CommandHandler("time", time_cmd))
    app.add_handler(CommandHandler("debug_holidays", debug_holidays_cmd))
    logger.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
