# handlers.py
import logging
from datetime import datetime

from telegram.constants import ChatType
from telegram import Update, ChatMemberAdministrator, ChatMemberOwner
from telegram.ext import ContextTypes
from config import DEFAULT_JOB_HOUR, DEFAULT_JOB_MINUTE

from db import (
    register_chat,
    chat_exists,
    set_chat_enabled,
    set_chat_time,
    get_all_chats_with_settings,
    add_birthday,
    get_today_birthdays,
    list_birthdays,
    delete_birthday,
    list_birthdays_by_user,
    delete_birthday_by_user,
)
from holidays import get_today_holidays
from yandex_gpt import generate_birthday_text

logger = logging.getLogger(__name__)

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return False

    # В личке считаем, что у себя каждый «админ», чтобы бот не падал
    if chat.type == "private":
        return True

    try:
        admins = await chat.get_administrators()
        # user считается админом, если его id есть в списке админов чата
        return any(a.user.id == user.id for a in admins)
    except Exception as e:
        logger.exception("Error checking admin rights: %s", e)
        return False

# ==== DAILY SCHEDULER ====

async def send_congrats_for_chat(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    holidays = get_today_holidays()
    birthdays = get_today_birthdays(chat_id)

    parts = []

    if holidays:
        holidays_text = "\n".join(f"• {h}" for h in holidays)
        parts.append("🎊 Праздники сегодня:\n" + holidays_text)

    if birthdays:
        lines = []
        for user_id, name, _ in birthdays:
            mention = f"<a href=\"tg://user?id={user_id}\">{name}</a>"
            lines.append(generate_birthday_text(mention))
        parts.append("🎂 Дни рождения сегодня:\n" + "\n".join(lines))

    if not parts:
        return

    text = "\n\n".join(parts)

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

async def scheduler_tick(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    now_h = now.hour
    now_m = now.minute

    chats = get_all_chats_with_settings(DEFAULT_JOB_HOUR, DEFAULT_JOB_MINUTE)
    for chat in chats:
        if not chat["enabled"]:
            continue
        if chat["hour"] == now_h and chat["minute"] == now_m:
            try:
                await send_congrats_for_chat(context, chat["chat_id"])
            except Exception as e:
                logger.exception(
                    "Error sending daily message to %s: %s", chat["chat_id"], e
                )


# ==== COMMAND HANDLERS ====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat:
            register_chat(chat.id, DEFAULT_JOB_HOUR, DEFAULT_JOB_MINUTE)

    await update.message.reply_text(
        "Привет! Я буду напоминать о праздниках и днях рождения.\n\n"
        "Команды:\n"
        "/bday DD.MM Имя — добавить день рождения\n"
        "/list_my_bdays — показать твои записи\n"
        "/del_my_bday ID — удалить свою запись\n\n"
        "Команды только для админов:\n"
        "/list_bdays — все дни рождения\n"
        "/del_bday ID — удалить любую запись\n"
        "/enable — включить ежедневные поздравления\n"
        "/disable — выключить ежедневные поздравления\n"
        "/time HH:MM — установить время поздравления"
    )


async def add_chat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat:
        return

    if chat_exists(chat.id):
        await update.message.reply_text(
            "Этот чат уже есть в списке для ежедневных поздравлений."
        )
    else:
        register_chat(chat.id, DEFAULT_JOB_HOUR, DEFAULT_JOB_MINUTE)
        await update.message.reply_text(
            f"Чат {chat.id} добавлен в список для ежедневных поздравлений."
        )


async def bday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message  # вместо update.message
    if chat:
        register_chat(chat.id, DEFAULT_JOB_HOUR, DEFAULT_JOB_MINUTE)

    if not context.args or len(context.args) < 2:
        if message:
            await message.reply_text(
                "Формат: /bday DD.MM Имя\nНапример: /bday 06.02 Иван"
            )
        return

    date_part = context.args[0]
    name = " ".join(context.args[1:])

    try:
        day, month = map(int, date_part.split("."))
        date_str = f"2000-{month:02d}-{day:02d}"
    except Exception:
        if message:
            await message.reply_text("Неверный формат даты, нужно DD.MM")
        return

    user = update.effective_user
    if not (chat and user and message):
        return

    add_birthday(user.id, chat.id, name, date_str)
    await message.reply_text(
        f"Записал день рождения: {name} — {date_part}"
    )

async def list_my_bdays_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    rows = list_birthdays_by_user(chat.id, user.id)
    if not rows:
        await update.message.reply_text("У тебя пока нет записанных дней рождения в этом чате.")
        return

    lines = []
    for rec_id, name, date_str in rows:
        _, m, d = date_str.split("-")
        lines.append(f"{rec_id}: {d}.{m} — {name}")

    text = "Твои дни рождения в этом чате:\n" + "\n".join(lines)
    await update.message.reply_text(text)


async def del_my_bday_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    if not context.args:
        await update.message.reply_text("Формат: /del_my_bday ID\nID смотри в /list_my_bdays")
        return

    try:
        rec_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")
        return

    if delete_birthday_by_user(chat.id, user.id, rec_id):
        await update.message.reply_text(f"Твоя запись с ID {rec_id} удалена.")
    else:
        await update.message.reply_text("Такой записи у тебя нет.")


async def list_bdays_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat:
        return

    if not await is_admin(update, context):
        await update.message.reply_text("Эта команда доступна только администраторам чата.")
        return

    rows = list_birthdays(chat.id)
    if not rows:
        await update.message.reply_text("В этом чате пока нет записанных дней рождения.")
        return

    lines = []
    for rec_id, user_id, name, date_str in rows:
        _, m, d = date_str.split("-")
        lines.append(f"{rec_id}: {d}.{m} — {name} (user_id={user_id})")

    text = "Список дней рождения:\n" + "\n".join(lines)
    await update.message.reply_text(text)


async def del_bday_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat:
        return

    if not await is_admin(update, context):
        await update.message.reply_text("Эта команда доступна только администраторам чата.")
        return

    if not context.args:
        await update.message.reply_text("Формат: /del_bday ID\nID смотри в /list_bdays")
        return

    try:
        rec_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")
        return

    if delete_birthday(chat.id, rec_id):
        await update.message.reply_text(f"Запись с ID {rec_id} удалена.")
    else:
        await update.message.reply_text("Такой записи нет в этом чате.")


async def enable_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat:
        return

    if not await is_admin(update, context):
        await update.message.reply_text("Эта команда доступна только администраторам чата.")
        return

    register_chat(chat.id, DEFAULT_JOB_HOUR, DEFAULT_JOB_MINUTE)
    set_chat_enabled(chat.id, True)
    await update.message.reply_text("Ежедневные поздравления включены для этого чата.")


async def disable_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat:
        return

    if not await is_admin(update, context):
        await update.message.reply_text("Эта команда доступна только администраторам чата.")
        return

    register_chat(chat.id, DEFAULT_JOB_HOUR, DEFAULT_JOB_MINUTE)
    set_chat_enabled(chat.id, False)
    await update.message.reply_text("Ежедневные поздравления отключены для этого чата.")


async def time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat:
        return

    if not await is_admin(update, context):
        await update.message.reply_text("Эта команда доступна только администраторам чата.")
        return

    if not context.args:
        await update.message.reply_text(
            "Формат: /time HH:MM\nНапример: /time 09:00"
        )
        return

    time_str = context.args[0]
    try:
        hour_str, minute_str = time_str.split(":")
        hour = int(hour_str)
        minute = int(minute_str)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except Exception:
        await update.message.reply_text("Неверный формат времени, нужно HH:MM (00–23:59).")
        return

    register_chat(chat.id, DEFAULT_JOB_HOUR, DEFAULT_JOB_MINUTE)
    set_chat_time(chat.id, hour, minute)
    await update.message.reply_text(
        f"Время ежедневных поздравлений для этого чата установлено на {hour:02d}:{minute:02d}."
    )
async def debug_holidays_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    if not chat or not message:
        return

    holidays = get_today_holidays()
    if not holidays:
        await message.reply_text("API праздников вернуло пусто на сегодня.")
        return

    text = "🎊 Праздники сегодня (debug):\n" + "\n".join(f"• {h}" for h in holidays)
    await message.reply_text(text)
