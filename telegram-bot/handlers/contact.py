import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from config import ADMIN_CHAT_ID
from utils.keyboards import main_menu_keyboard, cancel_keyboard

logger = logging.getLogger(__name__)

CONTACT_MSG = 0


async def contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "💬 *Admin ထံ မက်ဆေ့ပို့မည်*\n\n"
        "Admin ထံ ပေးပို့လိုသော စာကို ရိုက်ထည့်ပါ။\n"
        "_(မေးခွန်း၊ ပြဿနာ၊ သို့မဟုတ် မှတ်ချက် မဆိုရပါ)_",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )
    return CONTACT_MSG


async def receive_contact_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    text = update.message.text.strip()

    admin_text = (
        f"📩 *ဖောက်သည် မက်ဆေ့*\n\n"
        f"👤 နာမည်: {user.full_name}\n"
        f"🙋 Username: @{user.username or '-'}\n"
        f"🆔 User ID: `{user.id}`\n\n"
        f"💬 *မက်ဆေ့:*\n{text}"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_text,
            parse_mode="Markdown",
        )
        await update.message.reply_text(
            "✅ *မက်ဆေ့ပေးပို့ပြီးပါပြီ!*\n\n"
            "Admin မှ မကြာမီ ပြန်လည်ဆက်သွယ်ပါမည်။",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        logger.error(f"Contact forward error: {e}")
        await update.message.reply_text(
            "⚠️ မက်ဆေ့ပေးပို့ရာတွင် အမှားဖြစ်ပွားပါသည်။ နောက်မှ ထပ်ကြိုးစားပါ။",
            reply_markup=main_menu_keyboard(),
        )

    return ConversationHandler.END


async def cancel_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        await query.message.reply_text(
            "❌ ပယ်ဖျက်ပြီ။\n\nဘာလုပ်ချင်ပါသလဲ?",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.message.reply_text(
            "❌ ပယ်ဖျက်ပြီ။\n\nဘာလုပ်ချင်ပါသလဲ?",
            reply_markup=main_menu_keyboard(),
        )
    return ConversationHandler.END


async def restart_from_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    from handlers.start import start_command
    await start_command(update, context)
    return ConversationHandler.END


def get_contact_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(contact_start, pattern="^contact_admin$"),
        ],
        states={
            CONTACT_MSG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_contact_message),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_contact, pattern="^cancel$"),
            CommandHandler("cancel", cancel_contact),
            CommandHandler("start", restart_from_contact),
        ],
        allow_reentry=True,
        per_message=False,
    )
