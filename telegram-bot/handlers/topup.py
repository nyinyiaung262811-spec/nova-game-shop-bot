import re
import uuid
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
from config import (
    ADMIN_CHAT_ID,
    KPAY_ACCOUNT, KPAY_NAME,
    WAVEPAY_ACCOUNT, WAVEPAY_NAME,
)
from database import create_order, update_order, get_order, get_packages
from services import smileone
from utils.keyboards import (
    package_keyboard, payment_keyboard,
    confirm_keyboard, cancel_keyboard, main_menu_keyboard,
)

logger = logging.getLogger(__name__)

ACCOUNT_INPUT, SELECT_PACKAGE, SELECT_PAYMENT, UPLOAD_PROOF = range(4)

_ACCOUNT_RE = re.compile(r'^(\d+)\s*\((\d+)\)$')


def parse_account_input(text: str) -> tuple[str, str] | tuple[None, None]:
    text = text.strip()
    m = _ACCOUNT_RE.match(text)
    if m:
        return m.group(1), m.group(2)
    parts = text.split()
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        return parts[0], parts[1]
    return None, None


async def start_topup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    prompt = (
        "🎮 *MLBB Diamond ဖြည့်သွင်းခြင်း*\n\n"
        "Game ID နှင့် Server ID ကို တစ်ခါတည်း ရိုက်ပါ။\n\n"
        "အောက်ပါ format များ အသုံးပြုနိုင်သည်:\n"
        "`420082575(9959)`\n"
        "`420082575 (9959)`\n"
        "`420082575 9959`"
    )
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text(
            prompt, parse_mode="Markdown", reply_markup=cancel_keyboard()
        )
    else:
        await update.message.reply_text(
            prompt, parse_mode="Markdown", reply_markup=cancel_keyboard()
        )
    return ACCOUNT_INPUT


async def receive_account_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    game_id, server_id = parse_account_input(update.message.text)

    if not game_id:
        await update.message.reply_text(
            "⚠️ ဖတ်မရပါ။ Game ID နှင့် Server ID ကို တစ်ခါတည်း ရိုက်ပါ။\n\n"
            "ဥပမာများ:\n"
            "`420082575(9959)`\n"
            "`420082575 (9959)`\n"
            "`420082575 9959`",
            parse_mode="Markdown",
            reply_markup=cancel_keyboard(),
        )
        return ACCOUNT_INPUT

    context.user_data["game_id"] = game_id
    context.user_data["server_id"] = server_id

    msg = await update.message.reply_text("🔍 အကောင့် စစ်ဆေးနေသည်...")

    try:
        result = await smileone.check_user(game_id, server_id)
        if result.get("status") == 200 and result.get("username"):
            nickname = result["username"]
            context.user_data["nickname"] = nickname
            packages = await get_packages()
            await msg.edit_text(
                f"✅ *အကောင့် တွေ့ပြီ!*\n\n"
                f"👤 နာမည်: *{nickname}*\n"
                f"🆔 Game ID: `{game_id}`\n"
                f"🌐 Server ID: `{server_id}`\n\n"
                f"Diamond Package ရွေးချယ်ပါ:",
                parse_mode="Markdown",
                reply_markup=package_keyboard(packages),
            )
            return SELECT_PACKAGE
        else:
            await msg.edit_text(
                "❌ *အကောင့် မတွေ့ပါ။*\n\n"
                "Game ID နှင့် Server ID စစ်ဆေးပြီး ထပ်ကြိုးစားပါ။",
                parse_mode="Markdown",
                reply_markup=cancel_keyboard(),
            )
            return ACCOUNT_INPUT
    except Exception as e:
        logger.error(f"Smile.one check_user error: {e}")
        await msg.edit_text(
            "⚠️ အကောင့် စစ်ဆေး၍ မရသေးပါ။ နောက်မှ ထပ်ကြိုးစားပါ။",
            reply_markup=cancel_keyboard(),
        )
        return ACCOUNT_INPUT


async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    pkg_id = query.data.replace("pkg_", "")
    packages = await get_packages()
    package = next((p for p in packages if p["id"] == pkg_id), None)
    if not package:
        await query.answer("ရွေးချယ်မှု မမှန်ကန်ပါ။", show_alert=True)
        return SELECT_PACKAGE

    context.user_data["package"] = package
    nickname = context.user_data.get("nickname", "")
    game_id = context.user_data["game_id"]

    await query.edit_message_text(
        f"💎 *Package ရွေးချယ်ပြီ*\n\n"
        f"👤 {nickname} (`{game_id}`)\n"
        f"💎 Diamond: *{package['diamonds']}*\n"
        f"💵 ငွေပမာဏ: *{package['price']:,} MMK*\n\n"
        f"ငွေပေးချေမှုနည်းလမ်း ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=payment_keyboard(),
    )
    return SELECT_PAYMENT


async def select_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    method = query.data
    package = context.user_data["package"]
    nickname = context.user_data.get("nickname", "")
    game_id = context.user_data["game_id"]

    if method == "pay_kpay":
        context.user_data["payment_method"] = "KBZPay"
        account_info = (
            f"📱 *KBZPay*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"အကောင့်: `{KPAY_ACCOUNT}`\n"
            f"နာမည်: *{KPAY_NAME}*\n"
        )
    else:
        context.user_data["payment_method"] = "Wave Pay"
        account_info = (
            f"🌊 *Wave Pay*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"အကောင့်: `{WAVEPAY_ACCOUNT}`\n"
            f"နာမည်: *{WAVEPAY_NAME}*\n"
        )

    await query.edit_message_text(
        f"💳 *ငွေပေးချေမှု အသေးစိတ်*\n\n"
        f"👤 {nickname} (`{game_id}`)\n"
        f"💎 Diamond: *{package['diamonds']}*\n"
        f"💵 ငွေပမာဏ: *{package['price']:,} MMK*\n\n"
        f"{account_info}\n"
        f"*{package['price']:,} MMK* ငွေလွှဲပြီး ငွေပေးချေမှု screenshot ကို ဤနေရာတွင် ပေးပို့ပါ။",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )
    return UPLOAD_PROOF


async def receive_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        await update.message.reply_text(
            "📸 ငွေပေးချေမှု *screenshot* ပေးပို့ပါ။",
            parse_mode="Markdown",
            reply_markup=cancel_keyboard(),
        )
        return UPLOAD_PROOF

    photo = update.message.photo[-1]
    file_id = photo.file_id

    package = context.user_data["package"]
    game_id = context.user_data["game_id"]
    server_id = context.user_data["server_id"]
    nickname = context.user_data.get("nickname", "")
    payment_method = context.user_data["payment_method"]
    user = update.effective_user

    order_id = str(uuid.uuid4())[:8].upper()
    order_data = {
        "order_id": order_id,
        "user_id": user.id,
        "username": user.username or user.first_name,
        "game_id": game_id,
        "server_id": server_id,
        "nickname": nickname,
        "diamonds": package["diamonds"],
        "price": package["price"],
        "product_id": package["product_id"],
        "payment_method": payment_method,
    }
    await create_order(order_data)
    await update_order(order_id, {"proof_file_id": file_id})

    await update.message.reply_text(
        f"✅ *မှာယူမှု တင်ပြီပြီ!*\n\n"
        f"🔖 မှာယူမှု ID: `{order_id}`\n"
        f"💎 {package['diamonds']} Diamond → *{nickname}*\n"
        f"💵 {package['price']:,} MMK — {payment_method}\n\n"
        f"⏳ Admin အတည်ပြုခြင်းကို စောင့်ဆိုင်းပါ...\n"
        f"Diamond ဖြည့်ပြီးသောအခါ အကြောင်းကြားပါမည်။",
        parse_mode="Markdown",
    )

    admin_text = (
        f"🔔 *Diamond ဖြည့်သွင်းမှာယူမှု အသစ်*\n\n"
        f"🔖 မှာယူမှု ID: `{order_id}`\n"
        f"👤 နာမည်: *{nickname}*\n"
        f"🆔 Game ID: `{game_id}`\n"
        f"🌐 Server ID: `{server_id}`\n"
        f"💎 Diamond: *{package['diamonds']}*\n"
        f"💵 ငွေပမာဏ: *{package['price']:,} MMK*\n"
        f"💳 ငွေပေးချေမှု: {payment_method}\n"
        f"🙋 ဖောက်သည်: @{user.username or user.first_name} (ID: {user.id})"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=file_id,
        caption=admin_text,
        parse_mode="Markdown",
        reply_markup=confirm_keyboard(order_id),
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    context.user_data.clear()
    if query:
        await query.answer()
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        await query.message.reply_text(
            "❌ Diamond ဖြည့်ခြင်း ပယ်ဖျက်ပြီ။\n\nဘာလုပ်ချင်ပါသလဲ?",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.message.reply_text(
            "❌ Diamond ဖြည့်ခြင်း ပယ်ဖျက်ပြီ။\n\nဘာလုပ်ချင်ပါသလဲ?",
            reply_markup=main_menu_keyboard(),
        )
    return ConversationHandler.END


async def restart_from_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    from handlers.start import start_command
    await start_command(update, context)
    return ConversationHandler.END


def get_topup_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("topup", start_topup),
            CommandHandler("top_up", start_topup),
            CallbackQueryHandler(start_topup, pattern="^start_topup$"),
        ],
        states={
            ACCOUNT_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_account_input),
            ],
            SELECT_PACKAGE: [
                CallbackQueryHandler(select_package, pattern="^pkg_"),
            ],
            SELECT_PAYMENT: [
                CallbackQueryHandler(select_payment, pattern="^pay_"),
            ],
            UPLOAD_PROOF: [
                MessageHandler(filters.PHOTO, receive_proof),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_proof),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern="^cancel$"),
            CommandHandler("cancel", cancel),
            CommandHandler("start", restart_from_conversation),
        ],
        allow_reentry=True,
        per_message=False,
    )
