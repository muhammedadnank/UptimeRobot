import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from utils import is_authorized, init_api

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

API_ID          = int(os.environ.get("API_ID", "0"))
API_HASH        = os.environ.get("API_HASH", "")
BOT_TOKEN       = os.environ.get("BOT_TOKEN", "")
UPTIMEROBOT_KEY = os.environ.get("UPTIMEROBOT_API_KEY", "")

app = Client("uptime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ── /start ─────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("start") & filters.private)
async def cmd_start(client: Client, message: Message):
    if not is_authorized(message.from_user.id): return
    from handlers.callbacks import main_keyboard
    await message.reply(
        "👋 **UptimeRobot Bot**\n\n"
        "Full control of your UptimeRobot account from Telegram!\n\n"
        "📋 **Commands:**\n"
        "• /status — Monitor statuses\n"
        "• /stats — Uptime & response times\n"
        "• /alerts — Recent alert logs\n"
        "• /account — Account details\n"
        "• /add — Add new monitor\n"
        "• /pause `<id>` — Pause monitor\n"
        "• /resume `<id>` — Resume monitor\n"
        "• /delete `<id>` — Delete monitor\n"
        "• /contacts — Alert contacts\n"
        "• /addcontact — Add alert contact\n"
        "• /delcontact `<id>` — Delete contact\n"
        "• /mwindow — Maintenance windows\n"
        "• /addmwindow — Add window\n"
        "• /delmwindow `<id>` — Delete window\n"
        "• /psp — Public status pages\n"
        "• /addpsp — Add status page\n"
        "• /delpsp `<id>` — Delete status page\n"
        "• /menu — Interactive panel",
        reply_markup=main_keyboard(),
        quote=True,
    )

# ── /menu ──────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("menu") & filters.private)
async def cmd_menu(client: Client, message: Message):
    if not is_authorized(message.from_user.id): return
    from handlers.callbacks import main_keyboard
    await message.reply(
        "🖥️ **UptimeRobot Control Panel**\nChoose an action:",
        reply_markup=main_keyboard(),
        quote=True,
    )


def main():
    for var, val in [
        ("API_ID", API_ID), ("API_HASH", API_HASH),
        ("BOT_TOKEN", BOT_TOKEN), ("UPTIMEROBOT_API_KEY", UPTIMEROBOT_KEY),
    ]:
        if not val or val == 0:
            raise ValueError(f"❌ Environment variable '{var}' is not set!")

    # Initialize shared API instance
    init_api(UPTIMEROBOT_KEY)

    # Register all handlers
    from handlers import monitors, account, contacts, mwindow, psp, callbacks
    monitors.register(app)
    account.register(app)
    contacts.register(app)
    mwindow.register(app)
    psp.register(app)
    callbacks.register(app)

    logger.info("🤖 UptimeRobot Bot starting with full feature set...")
    app.run()


if __name__ == "__main__":
    main()
