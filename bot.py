import os
import sys
import logging
import asyncio
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters
from pyrogram.types import Message
from db import init_db, get_user, upsert_user, delete_user
from handlers.middleware import check_all

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

API_ID    = int(os.environ.get("API_ID", "0"))
API_HASH  = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# FIX: Client created inside _run() — not at module level — to avoid the
# "Future attached to a different loop" RuntimeError on Python 3.14.
app: Client = None  # type: ignore[assignment]

NO_KEY_MSG = (
    "🔑 **API Key not set!**\n\n"
    "Please set your UptimeRobot API key first:\n"
    "`/setkey ur_your_api_key_here`\n\n"
    "Get your key from:\n"
    "dashboard.uptimerobot.com → Integrations & API → API"
)


# ── Core handlers ─────────────────────────────────────────────────────────────

def _register_core_handlers(client: Client):

    @client.on_message(filters.command("start") & filters.private)
    async def cmd_start(c: Client, message: Message):
        if await check_all(c, message):
            return
        from handlers.callbacks import main_keyboard
        from utils import get_api_for
        user = await get_user(message.from_user.id)
        has_key = bool(user and user.get("api_key"))
        name = message.from_user.first_name or "there"

        if has_key:
            # Fetch live account summary
            api = await get_api_for(message.from_user.id)
            summary = ""
            if api:
                acc = await api.get_account_details()
                if acc:
                    up     = acc.get("up_monitors", 0)
                    down   = acc.get("down_monitors", 0)
                    paused = acc.get("paused_monitors", 0)
                    summary = (
                        f"\n📊 **Your Monitors**\n"
                        f"✅ Up: `{up}`  🔴 Down: `{down}`  ⏸️ Paused: `{paused}`\n"
                    )
            await message.reply(
                f"👋 Welcome back, **{name}!**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"{summary}\n"
                f"Use the buttons below or type a command.\n\n"
                f"📋 **Quick Commands:**\n"
                f"• /status — Live monitor status\n"
                f"• /stats — Uptime & response times\n"
                f"• /alerts — Recent alert logs\n"
                f"• /add — Add new monitor\n"
                f"• /account — Account details\n"
                f"• /menu — Full control panel",
                reply_markup=main_keyboard(),
            )
        else:
            await message.reply(
                f"👋 Hello, **{name}!**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 **UptimeRobot Bot**\n"
                f"Full control of your UptimeRobot account from Telegram.\n\n"
                f"**🚀 Get Started:**\n"
                f"1️⃣ Go to [dashboard.uptimerobot.com](https://dashboard.uptimerobot.com)\n"
                f"2️⃣ My Settings → API Settings → Copy your key\n"
                f"3️⃣ Send: `/setkey ur_your_key_here`\n\n"
                f"**📋 All Commands:**\n"
                f"• /setkey `<key>` — Link your UptimeRobot API key\n"
                f"• /mykey — Check if key is set\n"
                f"• /deletekey — Remove stored key\n"
                f"• /status — Monitor statuses\n"
                f"• /stats — Uptime & response times\n"
                f"• /alerts — Recent alert logs\n"
                f"• /account — Account details\n"
                f"• /add — Add new monitor\n"
                f"• /pause `<id>` /resume `<id>` /delete `<id>`\n"
                f"• /contacts /addcontact /delcontact `<id>`\n"
                f"• /mwindow /addmwindow /delmwindow `<id>`\n"
                f"• /psp /addpsp /delpsp `<id>`\n"
                f"• /menu — Interactive control panel\n\n"
                f"👮 **Admin:** /botstats /broadcast /ban /unban /bannedlist /setfsub /delfsub /restart",
            )

    @client.on_message(filters.command("menu") & filters.private)
    async def cmd_menu(c: Client, message: Message):
        if await check_all(c, message):
            return
        from handlers.callbacks import main_keyboard
        from utils import get_api_for
        user = await get_user(message.from_user.id)
        if not user or not user.get("api_key"):
            await message.reply(NO_KEY_MSG)
            return
        api = await get_api_for(message.from_user.id)
        summary = "🖥️ **UptimeRobot Control Panel**\n"
        if api:
            acc = await api.get_account_details()
            if acc:
                up     = acc.get("up_monitors", 0)
                down   = acc.get("down_monitors", 0)
                paused = acc.get("paused_monitors", 0)
                summary += (
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"✅ Up: `{up}`  🔴 Down: `{down}`  ⏸️ Paused: `{paused}`\n"
                )
        summary += "\nChoose an action:"
        await message.reply(summary, reply_markup=main_keyboard())

    @client.on_message(filters.command("setkey") & filters.private)
    async def cmd_setkey(c: Client, message: Message):
        if await check_all(c, message):
            return
        args = message.command[1:]
        if not args:
            await message.reply(
                "Usage: `/setkey <api_key>`\n\n"
                "Accepted formats:\n"
                "• Main API key: `u1234567-xxxxxxxxxxxxxxxxxxxx`\n"
                "• Monitor key: `ur_xxxxxxxxxxxxxxxxxxxx`\n\n"
                "Get your key from:\n"
                "dashboard.uptimerobot.com → Integrations & API → API"
            )
            return
        api_key = args[0].strip()
        if not re.match(r"^(ur_[a-f0-9]+|u[0-9]+-[a-f0-9]+)$", api_key):
            await message.reply(
                "⚠️ Invalid key format.\n\n"
                "Accepted formats:\n"
                "• Main API key: `u1234567-xxxxxxxxxxxxxxxxxxxx`\n"
                "• Monitor key: `ur_xxxxxxxxxxxxxxxxxxxx`\n\n"
                "Find your key at:\n"
                "dashboard.uptimerobot.com → Integrations & API → API"
            )
            return
        ok = await upsert_user(message.from_user.id, api_key)
        if ok:
            await message.reply(
                "✅ **API key saved!**\n\n"
                "Your UptimeRobot account is now linked.\n"
                "Use /menu or /status to get started."
            )
        else:
            await message.reply("❌ Failed to save API key. Please try again.")

    @client.on_message(filters.command("mykey") & filters.private)
    async def cmd_mykey(c: Client, message: Message):
        if await check_all(c, message):
            return
        user = await get_user(message.from_user.id)
        if not user or not user.get("api_key"):
            await message.reply("❌ No API key set.\n\nUse `/setkey ur_your_key` to set one.")
            return
        key = user["api_key"]
        masked = key[:6] + "••••••••" + key[-4:]
        await message.reply(
            f"✅ **API key is set**\n\n"
            f"🔑 Key: `{masked}`\n\n"
            f"Use `/deletekey` to remove it."
        )

    @client.on_message(filters.command("deletekey") & filters.private)
    async def cmd_deletekey(c: Client, message: Message):
        if await check_all(c, message):
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Yes, delete", callback_data="confirm_deletekey"),
            InlineKeyboardButton("❌ Cancel",       callback_data="cancel"),
        ]])
        await message.reply(
            "⚠️ **Are you sure you want to delete your API key?**\n"
            "You will need to set it again to use the bot.",
            reply_markup=markup,
        )

    # ── check_fsub callback (force-sub retry button) ──────────────────────────
    @client.on_callback_query(filters.regex("^check_fsub$"))
    async def cb_check_fsub(c: Client, query):
        from handlers.middleware import check_force_sub as _cfs
        from pyrogram.errors import MessageNotModified
        still_blocked = await _cfs(c, query.message)
        if not still_blocked:
            await query.answer("✅ Verified! You can now use the bot.", show_alert=True)
            try:
                await query.message.delete()
            except Exception:
                pass
        else:
            await query.answer("❌ You haven't joined yet!", show_alert=True)


# ── Dummy HTTP server (keeps Render Web Service happy) ────────────────────────

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        pass  # silence access logs


def _start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("🌐 Health server started on port %d", port)


def main():
    # Start health server IMMEDIATELY — before any validation or DB calls
    # so Render's port scanner sees the open port right away.
    _start_health_server()

    for var, val in [
        ("API_ID", API_ID), ("API_HASH", API_HASH),
        ("BOT_TOKEN", BOT_TOKEN),
    ]:
        if not val or val == 0:
            raise ValueError(f"❌ Environment variable '{var}' is not set!")

    if not os.environ.get("MONGODB_URI"):
        raise ValueError("❌ Environment variable 'MONGODB_URI' is not set!")

    async def _run():
        global app

        # FIX: Create Client inside the running event loop so all internal
        # asyncio primitives are bound to the same loop asyncio.run() created.
        app = Client(
            "uptime_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
        )

        # Register handlers
        _register_core_handlers(app)
        from handlers import monitors, account, contacts, mwindow, psp, callbacks, admin, inline
        monitors.register(app)
        account.register(app)
        contacts.register(app)
        mwindow.register(app)
        psp.register(app)
        callbacks.register(app)
        admin.register(app)
        inline.register(app)        # ← inline search

        await init_db()
        await app.start()
        logger.info("🤖 UptimeRobot Bot started (multi-user, MongoDB).")
        await asyncio.Event().wait()

    asyncio.run(_run())


if __name__ == "__main__":
    main()
