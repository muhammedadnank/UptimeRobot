from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils import get_api_for
from handlers.middleware import check_banned, check_force_sub
from handlers.monitors import _set_state

MW_TYPE   = {1:"Once", 2:"Daily", 3:"Weekly", 4:"Monthly"}
MW_STATUS = {0:"Paused", 1:"Active"}
NO_KEY_MSG = "🔑 No API key set. Use /setkey to link your UptimeRobot account."


def register(app: Client):

    @app.on_message(filters.command("mwindow") & filters.private)
    async def cmd_mwindow(client: Client, message: Message):
        if await check_banned(client, message):
            return
        if await check_force_sub(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        sent    = await message.reply("⏳ Fetching maintenance windows…")
        windows = await api.get_mwindows()
        if not windows:
            await sent.edit_text("🪟 No maintenance windows found.\n\nUse /addmwindow to create one.")
            return
        lines = ["🪟 **Maintenance Windows**\n"]
        for w in windows:
            lines.append(
                f"🕐 **{w.get('friendly_name', 'No name')}**\n"
                f"   🔁 {MW_TYPE.get(w.get('type', 0), 'Unknown')}  •  {MW_STATUS.get(w.get('status', 0), 'Unknown')}\n"
                f"   ⏰ Start: `{w.get('start_time', '?')}`  •  ⏱ Duration: `{w.get('duration', '?')}` min\n"
                f"   🆔 `{w.get('id', '')}`\n"
            )
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("➕ Add Window", callback_data="add_mwindow"),
            InlineKeyboardButton("🔄 Refresh",    callback_data="mwindow"),
        ]])
        await sent.edit_text("\n".join(lines), reply_markup=markup)

    @app.on_message(filters.command("addmwindow") & filters.private)
    async def cmd_addmwindow(client: Client, message: Message):
        if await check_banned(client, message):
            return
        if await check_force_sub(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        _set_state(message.from_user.id, "mw_name")
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
        await message.reply(
            "🪟 **New Maintenance Window**\n\nStep 1 — Enter a **name**:",
            reply_markup=markup,
        )

    @app.on_message(filters.command("delmwindow") & filters.private)
    async def cmd_delmwindow(client: Client, message: Message):
        if await check_banned(client, message):
            return
        if await check_force_sub(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
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
