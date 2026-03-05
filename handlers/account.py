from pyrogram import Client, filters
from pyrogram.types import Message
from utils import get_api_for
from handlers.middleware import check_banned, check_force_sub

NO_KEY_MSG = "🔑 No API key set. Use /setkey to link your UptimeRobot account."


def register(app: Client):

    @app.on_message(filters.command("account") & filters.private)
    async def cmd_account(client: Client, message: Message):
        if await check_banned(client, message):
            return
        if await check_force_sub(client, message):
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
        limit    = acc.get("monitor_limit", "?")
        interval = acc.get("monitor_interval", "?")
        text = (
            "👤 **Account Details**\n\n"
            f"📧 Email: `{acc.get('email', '?')}`\n"
            f"📊 Monitors: `{used}` / `{limit}`\n"
            f"⏱ Check interval: every `{interval}` min\n\n"
            f"✅ Up: `{acc.get('up_monitors', 0)}`\n"
            f"🔴 Down: `{acc.get('down_monitors', 0)}`\n"
            f"⏸️ Paused: `{acc.get('paused_monitors', 0)}`"
        )
        await sent.edit_text(text)
