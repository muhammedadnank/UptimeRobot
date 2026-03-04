from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from utils import is_authorized, get_api

CONTACT_TYPE = {1:"SMS", 2:"Email", 3:"Webhook", 4:"Boxcar", 5:"Push Bullet",
                6:"Zapier", 7:"Pushover", 8:"HipChat", 9:"Slack", 10:"VictorOps",
                11:"Telegram", 14:"Splunk", 15:"Teams"}
STATUS_TEXT  = {0:"Paused", 1:"Active", 2:"Not Activated"}


def register(app: Client):

    @app.on_message(filters.command("contacts") & filters.private)
    async def cmd_contacts(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        sent     = await message.reply("⏳ Fetching alert contacts…", quote=True)
        contacts = await get_api().get_alert_contacts()
        if not contacts:
            await sent.edit_text("📭 No alert contacts found.\n\nUse /addcontact to add one.")
            return
        lines = ["📬 **Alert Contacts**\n"]
        for c in contacts:
            ctype  = CONTACT_TYPE.get(c.get("type", 0), f"Type {c.get('type')}")
            status = STATUS_TEXT.get(c.get("status", 0), "Unknown")
            name   = c.get("friendly_name", "No name")
            value  = c.get("value", "")
            cid    = c.get("id", "")
            lines.append(
                f"📌 **{name}**\n"
                f"   🔧 {ctype}  •  {status}\n"
                f"   📝 `{value}`\n"
                f"   🆔 `{cid}`\n"
            )
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("➕ Add Contact",    callback_data="add_contact"),
            InlineKeyboardButton("🔄 Refresh",        callback_data="contacts"),
        ]])
        await sent.edit_text("\n".join(lines), reply_markup=markup)

    @app.on_message(filters.command("addcontact") & filters.private)
    async def cmd_addcontact(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        from handlers.monitors import user_state
        uid = message.from_user.id
        user_state[uid] = {"step": "contact_name", "data": {}}
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
        await message.reply(
            "➕ **Add Alert Contact**\n\nStep 1 — Enter a **friendly name**:",
            reply_markup=markup, quote=True
        )

    @app.on_message(filters.command("delcontact") & filters.private)
    async def cmd_delcontact(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: `/delcontact <contact_id>`\nGet IDs from /contacts", quote=True)
            return
        cid = args[0]
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Yes, delete", callback_data=f"confirm_delcontact_{cid}"),
            InlineKeyboardButton("❌ Cancel",       callback_data="cancel"),
        ]])
        await message.reply(
            f"⚠️ Delete alert contact `{cid}`?",
            reply_markup=markup, quote=True
        )
