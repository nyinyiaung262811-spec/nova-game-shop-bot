from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def package_keyboard(packages: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for pkg in packages:
        label = f"💎 {pkg['diamonds']} Diamond — {pkg['price']:,} MMK"
        buttons.append([InlineKeyboardButton(label, callback_data=f"pkg_{pkg['id']}")])
    buttons.append([InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def payment_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("📱 KBZPay", callback_data="pay_kpay")],
        [InlineKeyboardButton("🌊 Wave Pay", callback_data="pay_wave")],
        [InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard(order_id: str) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("✅ အတည်ပြုပြီး ဖြည့်မည်", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton("❌ ငြင်းပယ်", callback_data=f"reject_{order_id}"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="cancel")]
    ])


def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("💎 Diamond ဖြည့်မယ်", callback_data="start_topup")],
        [InlineKeyboardButton("📋 ဝယ်ယူမှုမှတ်တမ်း", callback_data="my_orders")],
        [InlineKeyboardButton("💬 Admin နဲ့ပြောရန်", url="https://t.me/cedrix_2002")],
    ]
    return InlineKeyboardMarkup(buttons)
