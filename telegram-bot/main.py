import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from telegram import BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)

from config import BOT_TOKEN, ADMIN_CHAT_ID
from database import init_db
from handlers.start import (
    start_command, my_orders_callback, help_command,
    my_orders_command, admin_command, unknown_text,
)
from handlers.topup import get_topup_handler
from handlers.admin import get_admin_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    await init_db()
    logger.info("Database initialised.")

    await application.bot.set_my_commands([
        BotCommand("top_up",    "💎 Diamond ဖြည့်မယ်"),
        BotCommand("my_orders", "📋 မှာယူမှတ်တမ်း"),
        BotCommand("admin",     "💬 Admin နဲ့ပြောရန်"),
        BotCommand("help",      "❓ အကူအညီ"),
    ])
    logger.info("Bot commands registered.")

    if ADMIN_CHAT_ID:
        try:
            await application.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=(
                    "🤖 Bot စတင်ပြီပြီ!\n\n"
                    "Admin Commands:\n"
                    "/pending — စောင့်ဆိုင်းဆဲ မှာယူမှုများ\n"
                    "/stats — မှာယူမှု စာရင်းဇယား\n"
                    "/prices — Diamond Package ဈေးနှုန်းများ\n"
                    "/setprice <id> <price> — ဈေးနှုန်း ပြောင်းမည်\n"
                    "/hide <id> — Package ဖျောက်မည်\n"
                    "/show <id> — Package ပြမည်\n"
                    "/broadcast <msg> — ဖောက်သည် အားလုံးထံ မက်ဆေ့ပို့မည်\n"
                    "/search <game_id> — ဖောက်သည် မှာယူမှုများ ရှာဖွေမည်"
                ),
            )
        except Exception:
            pass
    logger.info("Bot is running.")


def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Exiting.")
        sys.exit(1)

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start",     start_command))
    app.add_handler(CommandHandler("help",      help_command))
    app.add_handler(CommandHandler("my_orders", my_orders_command))
    app.add_handler(CommandHandler("admin",     admin_command))

    app.add_handler(get_topup_handler())

    for handler in get_admin_handlers():
        app.add_handler(handler)

    app.add_handler(CallbackQueryHandler(my_orders_callback, pattern="^my_orders$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))

    logger.info("Starting polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
