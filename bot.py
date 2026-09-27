import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================
# НАСТРОЙКИ
# =========================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Не найдена переменная BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================
# КОМАНДЫ
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Я на связи!\n\n"
        "Пока я только тестовая версия бота.\n"
        "Напиши мне «бот» в сообщении — и я отвечу."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Доступные команды:\n\n"
        "/start — проверить работу бота\n"
        "/help — показать эту справку"
    )


# =========================
# ОБРАБОТКА СООБЩЕНИЙ
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower().strip()

    # Реагируем только на обращение к боту
    if "бот" not in text:
        return

    await update.message.reply_text(
        "Я тут 👀\n"
        "Вижу сообщение. Значит, связь с группой работает."
    )


# =========================
# ЗАПУСК
# =========================

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    logger.info("Бот запускается...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
