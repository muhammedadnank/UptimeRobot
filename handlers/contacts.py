from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils import get_api_for
from handlers.middleware import check_all
from handlers.monitors import _set_state

CONTACT_TYPE = {1:"SMS", 2:"Email", 3:"Webhook", 4:"Boxcar", 5:"Push Bullet",
                6:"Zapier", 7:"Pushover", 8:"HipChat", 9:"Slack", 10:"VictorOps",
                11:"Telegram", 14:"Splunk", 15:"Teams"}
STATUS_TEXT  = {0:"Paused", 1:"Active", 2:"Not Activated"}
NO_KEY_MSG   = "🔑 No API key set. Use /setkey to link your UptimeRobot account."


def register(app: Client):

    @app.on_message(filters.command("contacts") & filters.private)
    async def cmd_contacts(client: Client, message: Message):
        if await check_all(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        sent     = await message.reply("⏳ Fetching alert contacts…")
        contacts = await api.get_alert_contacts()
        if not contacts:
            await sent.edit_text("📭 No alert contacts found.\n\nUse /addcontact to add one.")
            return
        lines = ["📬 **Alert Contacts**\n"]
        for c in contacts:
            ctype  = CONTACT_TYPE.get(c.get("type", 0), f"Type {c.get('type')}")
            status = STATUS_TEXT.get(c.get("status", 0), "Unknown")
            lines.append(
                f"📌 **{c.get('friendly_name', 'No name')}**\n"
                f"   🔧 {ctype}  •  {status}\n"
                f"   📝 `{c.get('value', '')}`\n"
                f"   🆔 `{c.get('id', '')}`\n"
            )
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("➕ Add Contact", callback_data="add_contact"),
            InlineKeyboardButton("🔄 Refresh",     callback_data="contacts"),
        ]])
        await sent.edit_text("\n".join(lines), reply_markup=markup)

    @app.on_message(filters.command("addcontact") & filters.private)
    async def cmd_addcontact(client: Client, message: Message):
        if await check_all(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        _set_state(message.from_user.id, "contact_name")
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
        await message.reply(
            "➕ **Add Alert Contact**\n\nStep 1 — Enter a **friendly name**:",
            reply_markup=markup,
        )

    @app.on_message(filters.command("delcontact") & filters.private)
    async def cmd_delcontact(client: Client, message: Message):
        if await check_all(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: `/delcontact <contact_id>`\nGet IDs from /contacts")
            return
        cid = args[0]
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Yes, delete", callback_data=f"confirm_delcontact_{cid}"),
            InlineKeyboardButton("❌ Cancel",       callback_data="cancel"),
        ]])
        await message.reply(f"⚠️ Delete alert contact `{cid}`?", reply_markup=markup)
