from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils import is_authorized, get_api

MW_TYPE  = {1:"Once", 2:"Daily", 3:"Weekly", 4:"Monthly"}
MW_STATUS= {0:"Paused", 1:"Active"}


def register(app: Client):

    @app.on_message(filters.command("mwindow") & filters.private)
    async def cmd_mwindow(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        sent    = await message.reply("⏳ Fetching maintenance windows…")
        windows = await get_api().get_mwindows()
        if not windows:
            await sent.edit_text("🪟 No maintenance windows found.\n\nUse /addmwindow to create one.")
            return
        lines = ["🪟 **Maintenance Windows**\n"]
        for w in windows:
            wtype  = MW_TYPE.get(w.get("type", 0), "Unknown")
            status = MW_STATUS.get(w.get("status", 0), "Unknown")
            name   = w.get("friendly_name", "No name")
            start  = w.get("start_time", "?")
            dur    = w.get("duration", "?")
            wid    = w.get("id", "")
            lines.append(
                f"🕐 **{name}**\n"
                f"   🔁 {wtype}  •  {status}\n"
                f"   ⏰ Start: `{start}`  •  ⏱ Duration: `{dur}` min\n"
                f"   🆔 `{wid}`\n"
            )
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("➕ Add Window",  callback_data="add_mwindow"),
            InlineKeyboardButton("🔄 Refresh",     callback_data="mwindow"),
        ]])
        await sent.edit_text("\n".join(lines), reply_markup=markup)

    @app.on_message(filters.command("addmwindow") & filters.private)
    async def cmd_addmwindow(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        from handlers.monitors import _set_state
        uid = message.from_user.id
        _set_state(uid, "mw_name")
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
        await message.reply(
            "🪟 **New Maintenance Window**\n\nStep 1 — Enter a **name**:",
            reply_markup=markup
        )

    @app.on_message(filters.command("delmwindow") & filters.private)
    async def cmd_delmwindow(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: `/delmwindow <window_id>`\nGet IDs from /mwindow")
            return
        wid = args[0]
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Yes, delete", callback_data=f"confirm_delmwindow_{wid}"),
            InlineKeyboardButton("❌ Cancel",       callback_data="cancel"),
        ]])
        await message.reply(f"⚠️ Delete maintenance window `{wid}`?", reply_markup=markup)
