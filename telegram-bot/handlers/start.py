from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_orders
from utils.keyboards import main_menu_keyboard
from services.gemini import ask_gemini


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 *မင်္ဂလာပါ, {user.first_name}!*\n\n"
        f"💎 *MLBB Diamond ဖြည့်သွင်းဝန်ဆောင်မှု*\n"
        f"မြန်မာ ဂိမ်းဆော့သူများအတွက် လျင်မြန်၍ လုံခြုံသော Diamond ဖြည့်သွင်းဝန်ဆောင်မှု။\n\n"
        f"ဘာလုပ်ချင်ပါသလဲ?",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def my_orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    orders = await get_user_orders(user.id)

    if not orders:
        await query.edit_message_text(
            "📋 ဝယ်ယူမှုမှတ်တမ်း မရှိသေးပါ။ Diamond ဖြည့်မယ် နှိပ်ပြီး စတင်ပါ။",
            reply_markup=main_menu_keyboard(),
        )
        return

    status_label = {
        "pending":   "⏳ စောင့်ဆိုင်းဆဲ",
        "completed": "✅ ပြီးစီး",
        "rejected":  "❌ ငြင်းပယ်",
        "failed":    "⚠️ မအောင်မြင်",
    }

    text = "📋 *မကြာမီ မှာယူမှုများ*\n\n"
    for o in orders:
        label = status_label.get(o["status"], "❓")
        text += (
            f"{label}\n"
            f"🔖 `{o['order_id']}` — 💎 {o['diamonds']} Diamond\n"
            f"💵 {o['price']:,} MMK\n\n"
        )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Diamond ဖြည့်နည်း*\n\n"
        "1️⃣ 💎 *Diamond ဖြည့်မယ်* ကို နှိပ်ပါ\n"
        "2️⃣ Game ID နှင့် Server ID တစ်ခါတည်း ရိုက်ပါ\n"
        "   ဥပမာ — `420082575(9959)` သို့မဟုတ် `420082575 9959`\n"
        "3️⃣ Diamond Package ရွေးချယ်ပါ\n"
        "4️⃣ ငွေပေးချေမှုနည်းလမ်း ရွေးပါ (KBZPay / Wave Pay)\n"
        "5️⃣ ငွေပမာဏ လွှဲပြောင်းပြီး screenshot ပေးပို့ပါ\n"
        "6️⃣ Admin အတည်ပြုချိန် စောင့်ပါ ✅\n\n"
        "❓ မေးမြန်းလိုပါက 💬 *Admin နဲ့ပြောရန်* ကို နှိပ်ပါ။",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def my_orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orders = await get_user_orders(update.effective_user.id)

    if not orders:
        await update.message.reply_text(
            "📋 ဝယ်ယူမှုမှတ်တမ်း မရှိသေးပါ။ Diamond ဖြည့်မယ် နှိပ်ပြီး စတင်ပါ။",
            reply_markup=main_menu_keyboard(),
        )
        return

    status_label = {
        "pending":   "⏳ စောင့်ဆိုင်းဆဲ",
        "completed": "✅ ပြီးစီး",
        "rejected":  "❌ ငြင်းပယ်",
        "failed":    "⚠️ မအောင်မြင်",
    }

    text = "📋 *မကြာမီ မှာယူမှုများ*\n\n"
    for o in orders:
        label = status_label.get(o["status"], "❓")
        text += (
            f"{label}\n"
            f"🔖 `{o['order_id']}` — 💎 {o['diamonds']} Diamond\n"
            f"💵 {o['price']:,} MMK\n\n"
        )

    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=main_menu_keyboard()
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💬 *Admin နဲ့ပြောရန်*\n\nအောက်ပါ ခလုတ်ကို နှိပ်ပြီး Admin ထံ တိုက်ရိုက် ဆက်သွယ်နိုင်သည်။",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Admin နဲ့ပြောရန်", url="https://t.me/cedrix_2002")]
        ]),
    )


async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    await update.message.chat.send_action("typing")
    reply = await ask_gemini(user_message)
    await update.message.reply_text(reply, reply_markup=main_menu_keyboard())
