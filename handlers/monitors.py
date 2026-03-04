from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from uptime_robot import UptimeRobotAPI
from utils import is_authorized, get_api

STATUS_EMOJI = {0: "⏸️", 1: "🔍", 2: "✅", 8: "🟡", 9: "🔴"}
STATUS_TEXT  = {0: "Paused", 1: "Not Checked", 2: "Up", 8: "Seems Down", 9: "Down"}
TYPE_TEXT    = {1: "HTTP(s)", 2: "Keyword", 3: "Ping", 4: "Port", 5: "Heartbeat"}

# user_state stores multi-step conversation state per user
# format: {user_id: {"step": str, "data": dict}}
user_state: dict = {}


def register(app: Client):

    # ── /status ───────────────────────────────────────────────────────────────
    @app.on_message(filters.command("status") & filters.private)
    async def cmd_status(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        sent = await message.reply("⏳ Fetching monitors…", quote=True)
        text, markup = await build_status(get_api())
        await sent.edit_text(text, reply_markup=markup)

    # ── /stats ────────────────────────────────────────────────────────────────
    @app.on_message(filters.command("stats") & filters.private)
    async def cmd_stats(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        sent = await message.reply("⏳ Fetching stats…", quote=True)
        await sent.edit_text(await build_stats(get_api()))

    # ── /alerts ───────────────────────────────────────────────────────────────
    @app.on_message(filters.command("alerts") & filters.private)
    async def cmd_alerts(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        sent = await message.reply("⏳ Fetching alerts…", quote=True)
        await sent.edit_text(await build_alerts(get_api()))

    # ── /pause <id> ───────────────────────────────────────────────────────────
    @app.on_message(filters.command("pause") & filters.private)
    async def cmd_pause(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: `/pause <monitor_id>`\nGet IDs from /status", quote=True)
            return
        ok = await get_api().pause_monitor(args[0])
        await message.reply(
            f"⏸️ Monitor `{args[0]}` paused." if ok else f"❌ Failed to pause `{args[0]}`.",
            quote=True
        )

    # ── /resume <id> ──────────────────────────────────────────────────────────
    @app.on_message(filters.command("resume") & filters.private)
    async def cmd_resume(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: `/resume <monitor_id>`\nGet IDs from /status", quote=True)
            return
        ok = await get_api().resume_monitor(args[0])
        await message.reply(
            f"▶️ Monitor `{args[0]}` resumed." if ok else f"❌ Failed to resume `{args[0]}`.",
            quote=True
        )

    # ── /delete <id> ─────────────────────────────────────────────────────────
    @app.on_message(filters.command("delete") & filters.private)
    async def cmd_delete(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: `/delete <monitor_id>`\nGet IDs from /status", quote=True)
            return
        mid = args[0]
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Yes, delete", callback_data=f"confirm_delete_{mid}"),
            InlineKeyboardButton("❌ Cancel",       callback_data="cancel"),
        ]])
        await message.reply(
            f"⚠️ **Are you sure you want to delete monitor** `{mid}`?\nThis cannot be undone!",
            reply_markup=markup, quote=True
        )

    # ── /add — multi-step ─────────────────────────────────────────────────────
    @app.on_message(filters.command("add") & filters.private)
    async def cmd_add(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        uid = message.from_user.id
        user_state[uid] = {"step": "add_name", "data": {}}
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
        await message.reply(
            "➕ **Add New Monitor**\n\nStep 1/3 — Enter a **friendly name** for the monitor:",
            reply_markup=markup, quote=True
        )

    # ── Text message handler (multi-step state machine) ───────────────────────
    @app.on_message(filters.text & filters.private & ~filters.command([
        "start","menu","status","stats","alerts","pause","resume",
        "delete","add","account","contacts","addcontact","delcontact",
        "mwindow","addmwindow","delmwindow","psp","addpsp","delpsp"
    ]))
    async def handle_text(client: Client, message: Message):
        if not is_authorized(message.from_user.id): return
        uid  = message.from_user.id
        text = message.text.strip()
        state = user_state.get(uid)
        if not state:
            return

        step = state["step"]
        data = state["data"]

        # ── Add monitor steps ─────────────────────────────────────────────
        if step == "add_name":
            data["name"] = text
            state["step"] = "add_url"
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            await message.reply("Step 2/3 — Enter the **URL** to monitor:\n(e.g. `https://example.com`)", reply_markup=markup, quote=True)

        elif step == "add_url":
            if not text.startswith("http"):
                await message.reply("⚠️ URL must start with `http://` or `https://`. Try again:", quote=True)
                return
            data["url"] = text
            state["step"] = "add_type"
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🌐 HTTP(s)", callback_data="add_type_1"),
                    InlineKeyboardButton("🔑 Keyword", callback_data="add_type_2"),
                ],
                [
                    InlineKeyboardButton("📡 Ping",    callback_data="add_type_3"),
                    InlineKeyboardButton("🔌 Port",    callback_data="add_type_4"),
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
            ])
            await message.reply("Step 3/3 — Choose **monitor type**:", reply_markup=markup, quote=True)

        # ── Alert contact add steps ────────────────────────────────────────
        elif step == "contact_name":
            data["name"] = text
            state["step"] = "contact_type"
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📧 Email",    callback_data="ct_2"),
                    InlineKeyboardButton("💬 Telegram", callback_data="ct_11"),
                ],
                [
                    InlineKeyboardButton("🔔 Webhook",  callback_data="ct_3"),
                    InlineKeyboardButton("📱 SMS",      callback_data="ct_1"),
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
            ])
            await message.reply("Choose **contact type**:", reply_markup=markup, quote=True)

        elif step == "contact_value":
            data["value"] = text
            result = await get_api().new_alert_contact(data["type"], text, data.get("name",""))
            user_state.pop(uid, None)
            if result:
                cid = result.get("alertcontact", {}).get("id", "?")
                await message.reply(f"✅ Alert contact added!\nID: `{cid}`", quote=True)
            else:
                await message.reply("❌ Failed to add alert contact.", quote=True)

        # ── Maintenance window steps ───────────────────────────────────────
        elif step == "mw_name":
            data["name"] = text
            state["step"] = "mw_type"
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📅 Once",    callback_data="mw_type_1"),
                    InlineKeyboardButton("🔁 Daily",   callback_data="mw_type_2"),
                ],
                [
                    InlineKeyboardButton("📆 Weekly",  callback_data="mw_type_3"),
                    InlineKeyboardButton("🗓️ Monthly", callback_data="mw_type_4"),
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
            ])
            await message.reply("Choose **window type**:", reply_markup=markup, quote=True)

        elif step == "mw_time":
            # Expected: HH:MM
            if ":" not in text or len(text) != 5:
                await message.reply("⚠️ Format should be `HH:MM` (e.g. `02:00`). Try again:", quote=True)
                return
            data["start_time"] = text
            state["step"] = "mw_duration"
            await message.reply("Enter **duration in minutes** (e.g. `60` for 1 hour):", quote=True)

        elif step == "mw_duration":
            if not text.isdigit():
                await message.reply("⚠️ Please enter a number (minutes). Try again:", quote=True)
                return
            result = await get_api().new_mwindow(
                data["name"], data["mw_type"], data.get("value",""), data["start_time"], int(text)
            )
            user_state.pop(uid, None)
            if result:
                mid = result.get("mwindow", {}).get("id", "?")
                await message.reply(f"✅ Maintenance window created!\nID: `{mid}`", quote=True)
            else:
                await message.reply("❌ Failed to create maintenance window.", quote=True)

        # ── PSP add steps ──────────────────────────────────────────────────
        elif step == "psp_name":
            data["name"] = text
            state["step"] = "psp_confirm"
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🌐 All monitors", callback_data="psp_monitors_all"),
                    InlineKeyboardButton("🔍 Specific IDs", callback_data="psp_monitors_custom"),
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
            ])
            await message.reply(
                f"PSP name: **{text}**\n\nWhich monitors to include?",
                reply_markup=markup, quote=True
            )

        elif step == "psp_monitor_ids":
            data["monitors"] = text.replace(" ","")
            result = await get_api().new_psp(data["name"], monitors=data["monitors"])
            user_state.pop(uid, None)
            if result:
                pid = result.get("psp", {}).get("id", "?")
                await message.reply(f"✅ Status page created!\nID: `{pid}`", quote=True)
            else:
                await message.reply("❌ Failed to create status page.", quote=True)


# ── Builder helpers ───────────────────────────────────────────────────────────
async def build_status(api: UptimeRobotAPI) -> tuple[str, InlineKeyboardMarkup | None]:
    monitors = await api.get_monitors()
    if not monitors:
        return "❌ No monitors found or API error.", None
    lines = ["📊 **Monitor Status**\n"]
    up = down = paused = 0
    for m in monitors:
        s     = m.get("status", 1)
        emoji = STATUS_EMOJI.get(s, "❓")
        label = STATUS_TEXT.get(s, "Unknown")
        name  = m.get("friendly_name", m.get("url", "?"))
        mid   = m.get("id", "")
        mtype = TYPE_TEXT.get(m.get("type", 1), "Unknown")
        lines.append(f"{emoji} **{name}** `[{label}]`\n   🆔 `{mid}`  •  🔧 {mtype}")
        if s == 2:   up += 1
        elif s == 9: down += 1
        elif s == 0: paused += 1
    lines.append(f"\n✅ Up: {up}  🔴 Down: {down}  ⏸️ Paused: {paused}")
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Refresh", callback_data="status"),
        InlineKeyboardButton("📈 Stats",   callback_data="stats"),
        InlineKeyboardButton("🔔 Alerts",  callback_data="alerts"),
    ]])
    return "\n".join(lines), markup


async def build_stats(api: UptimeRobotAPI) -> str:
    monitors = await api.get_monitors(response_times=1, custom_uptime_ratios="7-30-90")
    if not monitors:
        return "❌ Could not fetch stats."
    lines = ["📈 **Monitor Stats**\n"]
    for m in monitors:
        name    = m.get("friendly_name", m.get("url", "?"))
        ratios  = m.get("custom_uptime_ratio", "").split("-")
        r7  = f"{ratios[0]}%" if len(ratios) > 0 else "N/A"
        r30 = f"{ratios[1]}%" if len(ratios) > 1 else "N/A"
        r90 = f"{ratios[2]}%" if len(ratios) > 2 else "N/A"
        rt_data = m.get("response_times", [])
        avg_rt  = "N/A"
        if rt_data:
            vals = [r["value"] for r in rt_data if r.get("value")]
            if vals:
                avg_rt = f"{round(sum(vals)/len(vals))} ms"
        lines.append(
            f"🖥️ **{name}**\n"
            f"   ⏱ Avg: `{avg_rt}` | 7d: `{r7}` | 30d: `{r30}` | 90d: `{r90}`\n"
        )
    return "\n".join(lines)


async def build_alerts(api: UptimeRobotAPI) -> str:
    monitors = await api.get_monitors(logs=1)
    if not monitors:
        return "❌ Could not fetch alert logs."
    lines = ["🔔 **Recent Alerts**\n"]
    found = False
    for m in monitors:
        name = m.get("friendly_name", m.get("url", "?"))
        logs = m.get("logs", [])[:3]
        if not logs:
            continue
        found = True
        lines.append(f"🖥️ **{name}**")
        for log in logs:
            lt = log.get("type", 0)
            dt = datetime.utcfromtimestamp(log.get("datetime", 0)).strftime("%Y-%m-%d %H:%M")
            icon, desc = ("🔴","Went DOWN") if lt==1 else ("✅","Came UP") if lt==2 else ("ℹ️",f"Event {lt}")
            reason = log.get("reason", {}).get("detail", "")
            lines.append(f"   {icon} `{dt}` — {desc}" + (f": _{reason}_" if reason else ""))
        lines.append("")
    if not found:
        lines.append("No recent alerts.")
    return "\n".join(lines)
