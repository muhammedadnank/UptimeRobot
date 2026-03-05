from datetime import datetime, timezone, timedelta
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.uptime_robot import UptimeRobotAPI
from app.core.api_cache import get_api_for
from app.handlers.middleware import check_all

STATE_TTL = 600  # 10 minutes

# {user_id: {"step": str, "data": dict, "ts": float}}
user_state: dict = {}


def _set_state(uid: int, step: str, data: dict = None):
    user_state[uid] = {"step": step, "data": data or {}, "ts": time.time()}


def _get_state(uid: int) -> dict | None:
    state = user_state.get(uid)
    if state and (time.time() - state["ts"]) > STATE_TTL:
        user_state.pop(uid, None)
        return None
    return state


NO_KEY_MSG = "🔑 No API key set. Use /setkey to link your UptimeRobot account."
IST = timezone(timedelta(hours=5, minutes=30))

STATUS_EMOJI = {0: "⏸️", 1: "🔍", 2: "✅", 8: "🟡", 9: "🔴"}
STATUS_TEXT  = {0: "Paused", 1: "Not Checked", 2: "Up", 8: "Seems Down", 9: "Down"}
TYPE_TEXT    = {1: "HTTP(s)", 2: "Keyword", 3: "Ping", 4: "Port", 5: "Heartbeat"}

PAGE_SIZE = 5  # monitors per page


# ── UI Helpers ────────────────────────────────────────────────────────────────

def _uptime_bar(ratio_str: str, length: int = 10) -> str:
    try:
        val = float(str(ratio_str).replace("%", ""))
    except (ValueError, AttributeError):
        return "N/A"
    filled = round(val / 100 * length)
    bar = "▓" * filled + "░" * (length - filled)
    badge = "🟢" if val >= 99 else "🟡" if val >= 95 else "🔴"
    return f"{badge} `{bar}` {val:.2f}%"


def _monitor_action_row(mid: str, status: int) -> list:
    toggle = (
        InlineKeyboardButton("▶️ Resume", callback_data=f"mon_resume_{mid}")
        if status == 0
        else InlineKeyboardButton("⏸️ Pause", callback_data=f"mon_pause_{mid}")
    )
    return [toggle, InlineKeyboardButton("🗑 Delete", callback_data=f"mon_delete_{mid}")]


def register(app: Client):

    @app.on_message(filters.command("status") & filters.private)
    async def cmd_status(client: Client, message: Message):
        if await check_all(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        sent = await message.reply("⏳ Fetching monitors…")
        text, markup = await build_status(api, page=0)
        await sent.edit_text(text, reply_markup=markup)

    @app.on_message(filters.command("stats") & filters.private)
    async def cmd_stats(client: Client, message: Message):
        if await check_all(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        sent = await message.reply("⏳ Fetching stats…")
        text, markup = await build_stats(api)
        await sent.edit_text(text, reply_markup=markup)

    @app.on_message(filters.command("alerts") & filters.private)
    async def cmd_alerts(client: Client, message: Message):
        if await check_all(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        sent = await message.reply("⏳ Fetching alerts…")
        text, markup = await build_alerts(api, filter_type="all")
        await sent.edit_text(text, reply_markup=markup)

    @app.on_message(filters.command("pause") & filters.private)
    async def cmd_pause(client: Client, message: Message):
        if await check_all(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: `/pause <monitor_id>`\nGet IDs from /status")
            return
        ok = await api.pause_monitor(args[0])
        await message.reply(
            f"⏸️ Monitor `{args[0]}` paused." if ok else f"❌ Failed to pause `{args[0]}`."
        )

    @app.on_message(filters.command("resume") & filters.private)
    async def cmd_resume(client: Client, message: Message):
        if await check_all(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: `/resume <monitor_id>`\nGet IDs from /status")
            return
        ok = await api.resume_monitor(args[0])
        await message.reply(
            f"▶️ Monitor `{args[0]}` resumed." if ok else f"❌ Failed to resume `{args[0]}`."
        )

    @app.on_message(filters.command("delete") & filters.private)
    async def cmd_delete(client: Client, message: Message):
        if await check_all(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        args = message.command[1:]
        if not args:
            await message.reply("Usage: `/delete <monitor_id>`\nGet IDs from /status")
            return
        mid = args[0]
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Yes, delete", callback_data=f"confirm_delete_{mid}"),
            InlineKeyboardButton("❌ Cancel",       callback_data="cancel"),
        ]])
        await message.reply(
            f"⚠️ **Delete monitor** `{mid}`?\nThis cannot be undone!",
            reply_markup=markup,
        )

    @app.on_message(filters.command("cancel") & filters.private)
    async def cmd_cancel(client: Client, message: Message):
        if await check_all(client, message):
            return
        user_state.pop(message.from_user.id, None)
        await message.reply("❌ Operation cancelled.")

    @app.on_message(filters.command("add") & filters.private)
    async def cmd_add(client: Client, message: Message):
        if await check_all(client, message):
            return
        api = await get_api_for(message.from_user.id)
        if not api:
            await message.reply(NO_KEY_MSG)
            return
        _set_state(message.from_user.id, "add_name")
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
        await message.reply(
            "➕ **Add New Monitor**\n\n"
            "Step 1 of 3\n"
            "━━━━━━━━━━━━━━━\n"
            "Enter a **friendly name** for this monitor:\n"
            "_e.g. My Website, API Server_",
            reply_markup=markup,
        )

    @app.on_message(filters.text & filters.private & ~filters.command([
        "start","menu","setkey","mykey","deletekey",
        "status","stats","alerts","pause","resume",
        "delete","add","cancel","account","contacts","addcontact","delcontact",
        "mwindow","addmwindow","delmwindow","psp","addpsp","delpsp",
        "broadcast","ban","unban","bannedlist","botstats","restart","setfsub","delfsub"
    ]))
    async def handle_text(client: Client, message: Message):
        if await check_all(client, message):
            return
        uid   = message.from_user.id
        text  = message.text.strip()
        state = _get_state(uid)
        if not state:
            return

        step = state["step"]
        data = state["data"]

        if step == "add_name":
            data["name"] = text
            state["step"] = "add_url"
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            await message.reply(
                "➕ **Add New Monitor**\n\n"
                "Step 2 of 3\n"
                "━━━━━━━━━━━━━━━\n"
                f"✏️ Name: `{text}`\n\n"
                "Enter the **URL** to monitor:\n"
                "_e.g. `https://example.com`_",
                reply_markup=markup,
            )

        elif step == "add_url":
            if not text.startswith("http"):
                text = "https://" + text
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
            await message.reply(
                "➕ **Add New Monitor**\n\n"
                "Step 3 of 3\n"
                "━━━━━━━━━━━━━━━\n"
                f"✏️ Name: `{data['name']}`\n"
                f"🔗 URL: `{text}`\n\n"
                "Choose **monitor type**:",
                reply_markup=markup,
            )

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
                    InlineKeyboardButton("💼 Slack",    callback_data="ct_9"),
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
            ])
            await message.reply(
                "Choose **contact type**:\n"
                "_(SMS requires a Pro plan)_",
                reply_markup=markup,
            )

        elif step == "contact_value":
            data["value"] = text
            api = await get_api_for(uid)
            if not api:
                await message.reply(NO_KEY_MSG)
                user_state.pop(uid, None)
                return
            result = await api.new_alert_contact(data["type"], text, data.get("name", ""))
            user_state.pop(uid, None)
            if result:
                cid = result.get("alertcontact", {}).get("id", "?")
                await message.reply(
                    f"✅ **Alert contact added!**\n\n"
                    f"📛 Name: `{data.get('name', '—')}`\n"
                    f"🆔 ID: `{cid}`"
                )
            else:
                await message.reply("❌ Failed to add alert contact.")

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
            await message.reply("Choose **window type**:", reply_markup=markup)

        elif step == "mw_value":
            hint = data.get("mw_value_hint", "")
            if not text.isdigit():
                await message.reply("⚠️ Please enter a number. Try again:")
                return
            val = int(text)
            if hint == "weekly" and not (1 <= val <= 7):
                await message.reply("⚠️ Enter a number between 1 (Mon) and 7 (Sun):")
                return
            if hint == "monthly" and not (1 <= val <= 28):
                await message.reply("⚠️ Enter a number between 1 and 28:")
                return
            data["mw_value"] = text
            state["step"] = "mw_time"
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            await message.reply(
                "Enter **start time** in `HH:MM` format (UTC):\n(e.g. `02:00` for 2 AM UTC)",
                reply_markup=markup,
            )

        elif step == "mw_time":
            valid_time = False
            if ":" in text and len(text) == 5:
                try:
                    hh, mm = text.split(":")
                    if hh.isdigit() and mm.isdigit() and 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59:
                        valid_time = True
                except ValueError:
                    pass
            if not valid_time:
                await message.reply("⚠️ Format: `HH:MM` (e.g. `02:00`). Try again:")
                return
            data["start_time"] = text
            state["step"] = "mw_duration"
            await message.reply("Enter **duration in minutes** (e.g. `60` for 1 hour):")

        elif step == "mw_duration":
            if not text.isdigit():
                await message.reply("⚠️ Please enter a number (minutes). Try again:")
                return
            api = await get_api_for(uid)
            if not api:
                await message.reply(NO_KEY_MSG)
                user_state.pop(uid, None)
                return
            result = await api.new_mwindow(
                data["name"], data["mw_type"], data.get("mw_value", ""), data["start_time"], int(text)
            )
            user_state.pop(uid, None)
            if result:
                mid = result.get("mwindow", {}).get("id", "?")
                await message.reply(
                    f"✅ **Maintenance window created!**\n\n"
                    f"📛 Name: `{data['name']}`\n"
                    f"🆔 ID: `{mid}`"
                )
            else:
                await message.reply("❌ Failed to create maintenance window.")

        elif step == "psp_name":
            data["name"] = text
            state["step"] = "psp_confirm"
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🌐 All monitors",  callback_data="psp_monitors_all"),
                    InlineKeyboardButton("🔍 Specific IDs",  callback_data="psp_monitors_custom"),
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
            ])
            await message.reply(
                f"📄 PSP name: **{text}**\n\nWhich monitors to include?",
                reply_markup=markup,
            )

        elif step == "psp_monitor_ids":
            data["monitors"] = text.replace(" ", "")
            api = await get_api_for(uid)
            if not api:
                await message.reply(NO_KEY_MSG)
                user_state.pop(uid, None)
                return
            result = await api.new_psp(data["name"], monitors=data["monitors"])
            user_state.pop(uid, None)
            if result:
                pid = result.get("psp", {}).get("id", "?")
                await message.reply(
                    f"✅ **Status page created!**\n\n"
                    f"📛 Name: `{data['name']}`\n"
                    f"🆔 ID: `{pid}`"
                )
            else:
                await message.reply("❌ Failed to create status page.")


# ── Builder helpers ───────────────────────────────────────────────────────────

async def build_status(api: UptimeRobotAPI, page: int = 0) -> tuple[str, InlineKeyboardMarkup | None]:
    monitors = await api.get_monitors()
    if not monitors:
        return "❌ No monitors found or API error.", None

    up     = sum(1 for m in monitors if m.get("status") == 2)
    down   = sum(1 for m in monitors if m.get("status") in (8, 9))
    paused = sum(1 for m in monitors if m.get("status") == 0)
    total  = len(monitors)

    total_pages  = max(1, -(-total // PAGE_SIZE))
    page         = max(0, min(page, total_pages - 1))
    page_monitors = monitors[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]

    lines = [
        "📊 **Monitor Status**",
        f"✅ `{up}` Up  •  🔴 `{down}` Down  •  ⏸️ `{paused}` Paused  •  📋 `{total}` Total",
        "─────────────────────",
    ]

    btn_rows = []
    for m in page_monitors:
        s     = m.get("status", 1)
        emoji = STATUS_EMOJI.get(s, "❓")
        label = STATUS_TEXT.get(s, "Unknown")
        name  = m.get("friendly_name", m.get("url", "?"))
        mid   = str(m.get("id", ""))
        mtype = TYPE_TEXT.get(m.get("type", 1), "Unknown")
        url   = m.get("url", "")
        short_url = url.replace("https://", "").replace("http://", "")[:35]

        lines.append(
            f"\n{emoji} **{name}**\n"
            f"   🔗 `{short_url}`  •  🔧 {mtype}\n"
            f"   Status: **{label}**  •  🆔 `{mid}`"
        )
        btn_rows.append(_monitor_action_row(mid, s))

    lines.append("\n─────────────────────")
    if total_pages > 1:
        lines.append(f"📄 Page {page + 1} of {total_pages}")

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"status_page_{page - 1}"))
    nav.append(InlineKeyboardButton("🔄 Refresh", callback_data=f"status_page_{page}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"status_page_{page + 1}"))

    btn_rows.append(nav)
    btn_rows.append([
        InlineKeyboardButton("📈 Stats",  callback_data="stats"),
        InlineKeyboardButton("🔔 Alerts", callback_data="alerts"),
        InlineKeyboardButton("🔙 Menu",   callback_data="menu"),
    ])

    return "\n".join(lines), InlineKeyboardMarkup(btn_rows)


async def build_stats(api: UptimeRobotAPI) -> tuple[str, InlineKeyboardMarkup]:
    monitors = await api.get_monitors(response_times=1, custom_uptime_ratios="7-30-90")
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("🔔 Alerts", callback_data="alerts"),
        ],
        [InlineKeyboardButton("🔙 Menu", callback_data="menu")],
    ])
    if not monitors:
        return "❌ Could not fetch stats.", markup

    lines = ["📈 **Monitor Stats**\n"]
    for m in monitors:
        name   = m.get("friendly_name", m.get("url", "?"))
        s      = m.get("status", 1)
        emoji  = STATUS_EMOJI.get(s, "❓")
        ratios = m.get("custom_uptime_ratio", "").split("-")
        r7     = ratios[0] if len(ratios) > 0 and ratios[0] else "N/A"
        r30    = ratios[1] if len(ratios) > 1 and ratios[1] else "N/A"
        r90    = ratios[2] if len(ratios) > 2 and ratios[2] else "N/A"

        rt_data = m.get("response_times", [])
        avg_rt  = "N/A"
        if rt_data:
            vals = [r["value"] for r in rt_data if r.get("value")]
            if vals:
                avg_rt = f"{round(sum(vals)/len(vals))} ms"

        lines.append(
            f"{emoji} **{name}**\n"
            f"   7d:  {_uptime_bar(r7)}\n"
            f"   30d: {_uptime_bar(r30)}\n"
            f"   90d: {_uptime_bar(r90)}\n"
            f"   ⏱ Avg response: `{avg_rt}`\n"
        )

    return "\n".join(lines), markup


async def build_alerts(api: UptimeRobotAPI, filter_type: str = "all") -> tuple[str, InlineKeyboardMarkup]:
    monitors = await api.get_monitors(logs=1)

    filter_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 All"        + (" ●" if filter_type == "all"  else ""), callback_data="alerts_all"),
            InlineKeyboardButton("🔴 Down only"  + (" ●" if filter_type == "down" else ""), callback_data="alerts_down"),
        ],
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("📈 Stats",  callback_data="stats"),
            InlineKeyboardButton("🔙 Menu",   callback_data="menu"),
        ],
    ])

    if not monitors:
        return "❌ Could not fetch alert logs.", filter_markup

    all_logs = []
    for m in monitors:
        name = m.get("friendly_name", m.get("url", "?"))
        for log in m.get("logs", []):
            lt = log.get("type", 0)
            if filter_type == "down" and lt != 1:
                continue
            all_logs.append({
                "name": name,
                "type": lt,
                "datetime": log.get("datetime", 0),
                "reason": log.get("reason", {}).get("detail", ""),
            })

    all_logs.sort(key=lambda x: x["datetime"], reverse=True)
    all_logs = all_logs[:15]

    if not all_logs:
        return "🔔 **Recent Alerts**\n\n✅ No alerts found.", filter_markup

    lines = ["🔔 **Recent Alerts** _(newest first)_\n"]
    for log in all_logs:
        lt   = log["type"]
        dt   = datetime.fromtimestamp(log["datetime"], tz=IST).strftime("%d %b, %I:%M %p")
        icon, desc = (
            ("🔴", "Went **DOWN**") if lt == 1
            else ("✅", "Came **UP**") if lt == 2
            else ("ℹ️", f"Event {lt}")
        )
        reason = f" — _{log['reason']}_" if log["reason"] else ""
        lines.append(f"{icon} `{dt}`  **{log['name']}**\n   {desc}{reason}\n")

    return "\n".join(lines), filter_markup
