from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.api_cache import get_api_for
from app.handlers.middleware import check_all

NO_KEY_MSG = "🔑 No API key set. Use /setkey to link your UptimeRobot account."


def register(app: Client):

    @app.on_message(filters.command("account") & filters.private)
    async def cmd_account(client: Client, message: Message):
        if await check_all(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        sent = await message.reply("⏳ Fetching account details…")
        acc  = await api.get_account_details()
        if not acc:
            await sent.edit_text("❌ Could not fetch account details.")
            return

        used     = acc.get("up_monitors", 0) + acc.get("down_monitors", 0) + acc.get("paused_monitors", 0)
        limit    = acc.get("monitor_limit", 1) or 1
        interval = acc.get("monitor_interval", "?")

        # Monitor usage progress bar
        filled = round(used / limit * 10)
        bar    = "▓" * filled + "░" * (10 - filled)
        pct    = round(used / limit * 100)

        # Plan badge
        plan = "🆓 Free" if limit <= 50 else "⭐ Pro"

        text = (
            "👤 **Account Details**\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📧 Email: `{acc.get('email', '?')}`\n"
            f"🏷️ Plan: {plan}\n"
            f"⏱ Check interval: every `{interval}` min\n\n"
            f"**📊 Monitor Usage**\n"
            f"`{bar}` {used} / {limit} ({pct}%)\n\n"
            f"✅ Up: `{acc.get('up_monitors', 0)}`\n"
            f"🔴 Down: `{acc.get('down_monitors', 0)}`\n"
            f"⏸️ Paused: `{acc.get('paused_monitors', 0)}`"
        )
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("🔙 Menu",   callback_data="menu"),
            ]
        ])
        await sent.edit_text(text, reply_markup=markup)
