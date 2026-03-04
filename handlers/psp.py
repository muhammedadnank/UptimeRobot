from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils import is_authorized, get_api

PSP_STATUS= {0:"Paused", 1:"Active"}


def register(app: Client):

    @app.on_message(filters.command("psp") & filters.private)
    async def cmd_psp(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        sent = await message.reply("⏳ Fetching status pages…", quote=True)
        psps = await get_api().get_psps()
        if not psps:
            await sent.edit_text("📄 No public status pages found.\n\nUse /addpsp to create one.")
            return
        lines = ["📄 **Public Status Pages**\n"]
        for p in psps:
            status    = PSP_STATUS.get(p.get("status", 0), "Unknown")
            name      = p.get("friendly_name", "No name")
            subdomain = p.get("custom_domain") or f"{p.get('subdomain','?')}.uptimerobot.com"
            pid       = p.get("id", "")
            monitors  = p.get("monitors", [])
            mon_count = len(monitors) if isinstance(monitors, list) else ("All" if monitors == 0 else monitors)
            lines.append(
                f"🌐 **{name}**\n"
                f"   🔗 `{subdomain}`\n"
                f"   📊 Monitors: `{mon_count}`  •  {status}\n"
                f"   🆔 `{pid}`\n"
            )
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("➕ Add Page",  callback_data="add_psp"),
            InlineKeyboardButton("🔄 Refresh",   callback_data="psp"),
        ]])
        await sent.edit_text("\n".join(lines), reply_markup=markup)

    @app.on_message(filters.command("addpsp") & filters.private)
    async def cmd_addpsp(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        from handlers.monitors import _set_state
        uid = message.from_user.id
        _set_state(uid, "psp_name")
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
        await message.reply(
            "📄 **New Public Status Page**\n\nEnter a **name** for the status page:",
            reply_markup=markup, quote=True
        )

    @app.on_message(filters.command("delpsp") & filters.private)
    async def cmd_delpsp(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: `/delpsp <psp_id>`\nGet IDs from /psp", quote=True)
            return
        pid = args[0]
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Yes, delete", callback_data=f"confirm_delpsp_{pid}"),
            InlineKeyboardButton("❌ Cancel",       callback_data="cancel"),
        ]])
        await message.reply(f"⚠️ Delete status page `{pid}`?", reply_markup=markup, quote=True)
