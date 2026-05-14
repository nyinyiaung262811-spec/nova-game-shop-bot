import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from config import ADMIN_CHAT_ID
from database import (
    get_order, update_order, get_pending_orders,
    get_packages, set_package_price, set_package_active,
    get_stats, get_all_user_ids, search_orders_by_game_id,
)
from services import smileone

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_CHAT_ID


async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("⛔ ခွင့်မပြုပါ။", show_alert=True)
        return

    order_id = query.data.replace("approve_", "")
    order = await get_order(order_id)

    if not order:
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ မှာယူမှု မတွေ့ပါ။",
            parse_mode="Markdown",
        )
        return

    if order["status"] != "pending":
        await query.edit_message_caption(
            caption=query.message.caption + f"\n\n⚠️ ဤမှာယူမှုသည် {order['status']} ဖြစ်နေပြီ။",
            parse_mode="Markdown",
        )
        return

    await query.edit_message_caption(
        caption=query.message.caption + "\n\n⏳ Diamond ဖြည့်သွင်းနေသည်...",
        parse_mode="Markdown",
    )

    try:
        result = await smileone.create_order(
            uid=order["game_id"],
            zone=order["server_id"],
            product_id=order["product_id"],
        )

        if result.get("status") == 200:
            smileone_order_id = result.get("order_id", "")
            await update_order(order_id, {
                "status": "completed",
                "smileone_order_id": smileone_order_id,
            })
            await query.edit_message_caption(
                caption=(
                    query.message.caption +
                    f"\n\n✅ *DIAMOND ဖြည့်သွင်းမှု အောင်မြင်!*\n"
                    f"Smile.one Order: `{smileone_order_id}`"
                ),
                parse_mode="Markdown",
            )
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=(
                    f"🎉 *Diamond ဖြည့်သွင်းပြီးပြီ!*\n\n"
                    f"🔖 မှာယူမှု ID: `{order_id}`\n"
                    f"👤 နာမည်: *{order['nickname']}*\n"
                    f"💎 *{order['diamonds']} Diamond* အကောင့်ထဲ ဖြည့်သွင်းပြီးပါပြီ!\n\n"
                    f"ဝယ်ယူမှုအတွက် ကျေးဇူးတင်ပါသည်! 🙏"
                ),
                parse_mode="Markdown",
            )
        else:
            error_msg = result.get("message", "Unknown error")
            await update_order(order_id, {"status": "failed"})
            await query.edit_message_caption(
                caption=(
                    query.message.caption +
                    f"\n\n❌ *Diamond ဖြည့်သွင်းမှု မအောင်မြင်ပါ!*\nSmile.one: {error_msg}"
                ),
                parse_mode="Markdown",
            )
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=(
                    f"⚠️ *Diamond ဖြည့်သွင်းမှု မအောင်မြင်ပါ*\n\n"
                    f"🔖 မှာယူမှု ID: `{order_id}`\n"
                    f"ဖြည့်သွင်းရာတွင် ပြဿနာ ဖြစ်ပွားပါသည်။\n"
                    f"မှာယူမှု ID ဖြင့် Admin ထံ ဆက်သွယ်ပါ။"
                ),
                parse_mode="Markdown",
            )
    except Exception as e:
        logger.error(f"Top up error for order {order_id}: {e}")
        await query.edit_message_caption(
            caption=query.message.caption + f"\n\n❌ အမှား: {str(e)[:100]}",
            parse_mode="Markdown",
        )


async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("⛔ ခွင့်မပြုပါ။", show_alert=True)
        return

    order_id = query.data.replace("reject_", "")
    order = await get_order(order_id)
    if not order:
        return

    await update_order(order_id, {"status": "rejected"})
    await query.edit_message_caption(
        caption=query.message.caption + "\n\n❌ *မှာယူမှု ငြင်းပယ်ခဲ့သည်။*",
        parse_mode="Markdown",
    )
    await context.bot.send_message(
        chat_id=order["user_id"],
        text=(
            f"❌ *မှာယူမှု ငြင်းပယ်ခဲ့သည်*\n\n"
            f"🔖 မှာယူမှု ID: `{order_id}`\n"
            f"ငွေပေးချေမှု အတည်ပြုနိုင်ခြင်း မရှိပါ။\n"
            f"မှားယွင်းသည်ဟု ထင်ပါက Admin ထံ ဆက်သွယ်ပါ။"
        ),
        parse_mode="Markdown",
    )


async def pending_orders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    orders = await get_pending_orders()
    if not orders:
        await update.message.reply_text("✅ စောင့်ဆိုင်းဆဲ မှာယူမှု မရှိပါ။")
        return
    text = f"📋 *စောင့်ဆိုင်းဆဲ မှာယူမှုများ ({len(orders)})*\n\n"
    for o in orders:
        text += (
            f"🔖 `{o['order_id']}` — 💎 {o['diamonds']} — "
            f"{o['nickname']} — {o['payment_method']}\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    s = await get_stats()
    sc = s["status_counts"]

    popular_lines = ""
    for diamonds, count in s["popular_packages"]:
        popular_lines += f"  • 💎 {diamonds} Diamond × {count} ကြိမ်\n"
    if not popular_lines:
        popular_lines = "  မှတ်တမ်း မရှိသေးပါ\n"

    text = (
        f"📊 *မှာယူမှု စာရင်းဇယား*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 *ယနေ့*\n"
        f"  မှာယူမှု: {s['today_orders']} ခု\n"
        f"  ဝင်ငွေ: {s['today_revenue']:,} MMK\n\n"
        f"🗓 *ဤလ*\n"
        f"  မှာယူမှု: {s['month_orders']} ခု\n"
        f"  ဝင်ငွေ: {s['month_revenue']:,} MMK\n\n"
        f"🏆 *စုစုပေါင်း*\n"
        f"  ဝင်ငွေ: {s['total_revenue']:,} MMK\n"
        f"  ဖောက်သည်: {s['total_customers']} ဦး\n\n"
        f"📋 *မှာယူမှု အခြေအနေ*\n"
        f"  ✅ ပြီးစီး: {sc.get('completed', 0)}\n"
        f"  ⏳ စောင့်ဆိုင်းဆဲ: {sc.get('pending', 0)}\n"
        f"  ❌ ငြင်းပယ်: {sc.get('rejected', 0)}\n"
        f"  ⚠️ မအောင်မြင်: {sc.get('failed', 0)}\n\n"
        f"🔥 *အရောင်းရဆုံး Package*\n"
        f"{popular_lines}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def prices_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    packages = await get_packages(active_only=False)
    if not packages:
        await update.message.reply_text("Package မရှိသေးပါ။")
        return
    lines = ["💎 *Diamond Package စာရင်း*\n"]
    for p in packages:
        status = "✅" if p["active"] else "🚫"
        lines.append(
            f"{status} ID `{p['id']}` — *{p['diamonds']}* 💎 — `{p['price']:,}` MMK"
        )
    lines.append(
        "\n*Commands:*\n"
        "`/setprice <id> <price>` — ဈေးနှုန်း ပြောင်းမည်\n"
        "`/hide <id>` — ဖောက်သည်မြင်မည့် Package ဖျောက်မည်\n"
        "`/show <id>` — Package ပြန်ပြမည်"
    )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def setprice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args or len(args) != 2:
        await update.message.reply_text(
            "သုံးပုံ: `/setprice <id> <price>`\n"
            "ဥပမာ: `/setprice 3 5500`\n\n"
            "Package ID များကြည့်ရန် /prices",
            parse_mode="Markdown",
        )
        return
    pkg_id, price_str = args[0], args[1]
    if not price_str.isdigit() or int(price_str) <= 0:
        await update.message.reply_text("⚠️ ဈေးနှုန်းသည် အပေါင်းကိန်း ဖြစ်ရမည်။")
        return
    new_price = int(price_str)
    updated = await set_package_price(pkg_id, new_price)
    if updated:
        packages = await get_packages(active_only=False)
        pkg = next((p for p in packages if p["id"] == pkg_id), None)
        await update.message.reply_text(
            f"✅ *ဈေးနှုန်း ပြောင်းလဲပြီ!*\n\n"
            f"💎 {pkg['diamonds'] if pkg else '?'} Diamond\n"
            f"💵 ဈေးနှုန်း အသစ်: *{new_price:,} MMK*",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"❌ Package ID `{pkg_id}` မတွေ့ပါ။ /prices စစ်ဆေးပါ။",
            parse_mode="Markdown",
        )


async def hide_package_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args:
        await update.message.reply_text("သုံးပုံ: `/hide <id>`", parse_mode="Markdown")
        return
    updated = await set_package_active(args[0], active=False)
    if updated:
        await update.message.reply_text(
            f"🚫 Package `{args[0]}` ကို ဖောက်သည်မှ *ဖျောက်ပြီ*။",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(f"❌ Package `{args[0]}` မတွေ့ပါ။", parse_mode="Markdown")


async def show_package_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args:
        await update.message.reply_text("သုံးပုံ: `/show <id>`", parse_mode="Markdown")
        return
    updated = await set_package_active(args[0], active=True)
    if updated:
        await update.message.reply_text(
            f"✅ Package `{args[0]}` ကို ဖောက်သည်မှ *မြင်သောနေရာ ပြန်ထားပြီ*။",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(f"❌ Package `{args[0]}` မတွေ့ပါ။", parse_mode="Markdown")


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "သုံးပုံ: `/search <game_id>`\n\nဥပမာ: `/search 420082575`",
            parse_mode="Markdown",
        )
        return

    game_id = context.args[0].strip()
    orders = await search_orders_by_game_id(game_id)

    if not orders:
        await update.message.reply_text(
            f"🔍 Game ID `{game_id}` အတွက် မှာယူမှု မတွေ့ပါ။",
            parse_mode="Markdown",
        )
        return

    status_label = {
        "pending":   "⏳ စောင့်ဆိုင်းဆဲ",
        "completed": "✅ ပြီးစီး",
        "rejected":  "❌ ငြင်းပယ်",
        "failed":    "⚠️ မအောင်မြင်",
    }

    first = orders[0]
    header = (
        f"🔍 *Game ID: `{game_id}` — မှာယူမှု မှတ်တမ်း*\n"
        f"👤 နာမည်: *{first['nickname'] or '-'}*\n"
        f"🙋 Telegram: @{first['username'] or '-'}\n"
        f"📦 စုစုပေါင်း: {len(orders)} ခု\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
    )

    lines = []
    total_spent = 0
    for o in orders:
        label = status_label.get(o["status"], "❓")
        lines.append(
            f"{label}\n"
            f"🔖 `{o['order_id']}` — 💎 {o['diamonds']} Diamond\n"
            f"💵 {o['price']:,} MMK — {o['payment_method']}\n"
            f"🕐 {o['created_at'][:16]}\n"
        )
        if o["status"] == "completed":
            total_spent += o["price"]

    footer = f"\n💰 *စုစုပေါင်း သုံးစွဲမှု: {total_spent:,} MMK*"

    await update.message.reply_text(
        header + "\n".join(lines) + footer,
        parse_mode="Markdown",
    )


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "သုံးပုံ: `/broadcast <message>`\n\n"
            "ဥပမာ: `/broadcast ကျွန်တော်တို့ဆိုင်သို့ ကြိုဆိုပါသည်!`\n\n"
            "ဖောက်သည် အားလုံးထံ မက်ဆေ့ပေးပို့ပါမည်။",
            parse_mode="Markdown",
        )
        return

    message = " ".join(context.args)
    user_ids = await get_all_user_ids()

    if not user_ids:
        await update.message.reply_text("⚠️ ဖောက်သည် မရှိသေးပါ။")
        return

    status_msg = await update.message.reply_text(
        f"📡 မက်ဆေ့ပေးပို့နေသည်... (ဖောက်သည် {len(user_ids)} ဦး)"
    )

    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📢 *အသိပေးချက်*\n\n{message}",
                parse_mode="Markdown",
            )
            sent += 1
        except Exception as e:
            logger.warning(f"Broadcast failed for {uid}: {e}")
            failed += 1

    await status_msg.edit_text(
        f"✅ *Broadcast ပြီးပါပြီ!*\n\n"
        f"📨 ပေးပို့အောင်မြင်: *{sent}* ဦး\n"
        f"❌ ပေးပို့မရ: *{failed}* ဦး",
        parse_mode="Markdown",
    )


def get_admin_handlers():
    return [
        CallbackQueryHandler(approve_order, pattern="^approve_"),
        CallbackQueryHandler(reject_order, pattern="^reject_"),
        CommandHandler("pending", pending_orders_cmd),
        CommandHandler("stats", stats_cmd),
        CommandHandler("prices", prices_cmd),
        CommandHandler("setprice", setprice_cmd),
        CommandHandler("hide", hide_package_cmd),
        CommandHandler("show", show_package_cmd),
        CommandHandler("broadcast", broadcast_cmd),
        CommandHandler("search", search_cmd),
    ]
