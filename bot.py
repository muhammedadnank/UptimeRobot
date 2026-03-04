import os
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from db import init_db, get_user, upsert_user, delete_user

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

API_ID    = int(os.environ.get("API_ID", "0"))
API_HASH  = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("uptime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

NO_KEY_MSG = (
    "🔑 **API Key not set!**\n\n"
    "Please set your UptimeRobot API key first:\n"
    "`/setkey ur_your_api_key_here`\n\n"
    "Get your key from:\n"
    "dashboard.uptimerobot.com → Integrations → API → Main API Key"
)

# ── /start ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("start") & filters.private)
async def cmd_start(client: Client, message: Message):
    from handlers.callbacks import main_keyboard
    user = await get_user(message.from_user.id)
    has_key = bool(user and user.get("api_key"))
    await message.reply(
        "👋 **UptimeRobot Bot**\n\n"
        "Full control of your UptimeRobot account from Telegram!\n\n"
        + ("✅ API key is set. You're ready to go!\n\n" if has_key else "⚠️ No API key set yet. Use /setkey to get started.\n\n")
        + "📋 **Commands:**\n"
        "• /setkey `<api_key>` — Set your UptimeRobot API key\n"
        "• /mykey — Check if your API key is set\n"
        "• /deletekey — Remove your stored API key\n"
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
        "• /cancel — Cancel current operation\n"
        "• /menu — Interactive panel",
        reply_markup=main_keyboard() if has_key else None,
    )

# ── /menu ─────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("menu") & filters.private)
async def cmd_menu(client: Client, message: Message):
    from handlers.callbacks import main_keyboard
    user = await get_user(message.from_user.id)
    if not user or not user.get("api_key"):
        await message.reply(NO_KEY_MSG)
        return
    await message.reply(
        "🖥️ **UptimeRobot Control Panel**\nChoose an action:",
        reply_markup=main_keyboard(),
    )

# ── /setkey ───────────────────────────────────────────────────────────────────
@app.on_message(filters.command("setkey") & filters.private)
async def cmd_setkey(client: Client, message: Message):
    args = message.command[1:]
    if not args:
        await message.reply(
            "Usage: `/setkey ur_your_api_key_here`\n\n"
            "Get your key from:\n"
            "dashboard.uptimerobot.com → Integrations → API → Main API Key"
        )
        return
    api_key = args[0].strip()
    if not api_key.startswith("ur_"):
        await message.reply("⚠️ Invalid key format. UptimeRobot API keys start with `ur_`")
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

# ── /mykey ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("mykey") & filters.private)
async def cmd_mykey(client: Client, message: Message):
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

# ── /deletekey ────────────────────────────────────────────────────────────────
@app.on_message(filters.command("deletekey") & filters.private)
async def cmd_deletekey(client: Client, message: Message):
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


def main():
    for var, val in [
        ("API_ID", API_ID), ("API_HASH", API_HASH),
        ("BOT_TOKEN", BOT_TOKEN),
    ]:
        if not val or val == 0:
            raise ValueError(f"❌ Environment variable '{var}' is not set!")

    if not os.environ.get("MONGODB_URI"):
        raise ValueError("❌ Environment variable 'MONGODB_URI' is not set!")

    # Register all handlers
    from handlers import monitors, account, contacts, mwindow, psp, callbacks
    monitors.register(app)
    account.register(app)
    contacts.register(app)
    mwindow.register(app)
    psp.register(app)
    callbacks.register(app)

    # Init DB indexes then run bot
    async def _run():
        await init_db()
        await app.start()
        logger.info("🤖 UptimeRobot Bot started (multi-user, MongoDB).")
        await asyncio.Event().wait()

    asyncio.run(_run())


if __name__ == "__main__":
    main()
