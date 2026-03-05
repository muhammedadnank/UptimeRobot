from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified
from app.core.api_cache import get_api_for
from app.core.db import delete_user, is_banned
from app.handlers.monitors import build_status, build_stats, build_alerts, user_state, _set_state, _get_state

NO_KEY_MSG = "🔑 No API key set. Use /setkey to link your UptimeRobot account."


async def safe_edit(message, text, reply_markup=None):
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except MessageNotModified:
        pass


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Status",     callback_data="status"),
            InlineKeyboardButton("📈 Stats",       callback_data="stats"),
            InlineKeyboardButton("🔔 Alerts",      callback_data="alerts"),
        ],
        [
            InlineKeyboardButton("➕ Add Monitor", callback_data="add_monitor"),
            InlineKeyboardButton("👤 Account",     callback_data="account"),
        ],
        [
            InlineKeyboardButton("📬 Contacts",    callback_data="contacts"),
            InlineKeyboardButton("🪟 Maint. Win.", callback_data="mwindow"),
            InlineKeyboardButton("📄 Status Page", callback_data="psp"),
        ],
    ])


def register(app: Client):

    @app.on_callback_query()
    async def on_callback(client: Client, query: CallbackQuery):
        await query.answer()
        data = query.data
        uid  = query.from_user.id

        banned, ban_reason = await is_banned(uid)
        if banned:
            await safe_edit(
                query.message,
                f"🚫 **You are banned from using this bot.**\n\n📝 Reason: _{ban_reason}_"
            )
            return

        api = await get_api_for(uid)

        # ── No-API-key actions ─────────────────────────────────────────────────
        if data == "cancel":
            user_state.pop(uid, None)
            await safe_edit(query.message, "❌ Operation cancelled.", reply_markup=None)
            return

        if data == "confirm_deletekey":
            ok = await delete_user(uid)
            await safe_edit(query.message,
                "🗑️ API key deleted." if ok else "❌ Failed to delete key."
            )
            return

        if data == "menu":
            if not api:
                await safe_edit(query.message, NO_KEY_MSG)
                return
            await safe_edit(
                query.message,
                "🖥️ **UptimeRobot Control Panel**\nChoose an action:",
                reply_markup=main_keyboard()
            )
            return

        if not api:
            await safe_edit(query.message, NO_KEY_MSG)
            return

        # ── Status with pagination ─────────────────────────────────────────────
        if data == "status":
            text, markup = await build_status(api, page=0)
            await safe_edit(query.message, text, reply_markup=markup)

        elif data.startswith("status_page_"):
            try:
                page = int(data.split("_")[-1])
            except ValueError:
                page = 0
            text, markup = await build_status(api, page=page)
            await safe_edit(query.message, text, reply_markup=markup)

        # ── Per-monitor quick actions ──────────────────────────────────────────
        elif data.startswith("mon_pause_"):
            mid = data.replace("mon_pause_", "")
            ok  = await api.pause_monitor(mid)
            if ok:
                text, markup = await build_status(api, page=0)
                await safe_edit(query.message, text, reply_markup=markup)
            else:
                await safe_edit(query.message, f"❌ Failed to pause monitor `{mid}`.")

        elif data.startswith("mon_resume_"):
            mid = data.replace("mon_resume_", "")
            ok  = await api.resume_monitor(mid)
            if ok:
                text, markup = await build_status(api, page=0)
                await safe_edit(query.message, text, reply_markup=markup)
            else:
                await safe_edit(query.message, f"❌ Failed to resume monitor `{mid}`.")

        elif data.startswith("mon_delete_"):
            mid = data.replace("mon_delete_", "")
            markup = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Yes, delete", callback_data=f"confirm_delete_{mid}"),
                InlineKeyboardButton("❌ Cancel",       callback_data="status"),
            ]])
            await safe_edit(
                query.message,
                f"⚠️ **Delete monitor** `{mid}`?\nThis cannot be undone!",
                reply_markup=markup
            )

        # ── Stats ──────────────────────────────────────────────────────────────
        elif data == "stats":
            text, markup = await build_stats(api)
            await safe_edit(query.message, text, reply_markup=markup)

        # ── Alerts with filter ─────────────────────────────────────────────────
        elif data in ("alerts", "alerts_all"):
            text, markup = await build_alerts(api, filter_type="all")
            await safe_edit(query.message, text, reply_markup=markup)

        elif data == "alerts_down":
            text, markup = await build_alerts(api, filter_type="down")
            await safe_edit(query.message, text, reply_markup=markup)

        # ── Account ───────────────────────────────────────────────────────────
        elif data == "account":
            acc = await api.get_account_details()
            if not acc:
                await safe_edit(query.message, "❌ Could not fetch account details.")
                return
            used  = acc.get("up_monitors", 0) + acc.get("down_monitors", 0) + acc.get("paused_monitors", 0)
            limit = acc.get("monitor_limit", 1) or 1
            filled = round(used / limit * 10)
            bar    = "▓" * filled + "░" * (10 - filled)
            pct    = round(used / limit * 100)

            text = (
                "👤 **Account Details**\n\n"
                f"📧 Email: `{acc.get('email', '?')}`\n"
                f"⏱ Check interval: every `{acc.get('monitor_interval', '?')}` min\n\n"
                f"**📊 Monitor Usage**\n"
                f"`{bar}` {used}/{limit} ({pct}%)\n\n"
                f"✅ Up: `{acc.get('up_monitors', 0)}`  "
                f"🔴 Down: `{acc.get('down_monitors', 0)}`  "
                f"⏸️ Paused: `{acc.get('paused_monitors', 0)}`"
            )
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="menu")]])
            await safe_edit(query.message, text, reply_markup=markup)

        # ── Contacts ──────────────────────────────────────────────────────────
        elif data in ("contacts", "add_contact"):
            if data == "add_contact":
                _set_state(uid, "contact_name")
                markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
                await safe_edit(query.message,
                    "➕ **Add Alert Contact**\n\nEnter a **friendly name**:",
                    reply_markup=markup
                )
                return
            contacts = await api.get_alert_contacts()
            if not contacts:
                text = "📭 No alert contacts found."
            else:
                CTYPE = {1:"SMS", 2:"Email", 3:"Webhook", 9:"Slack", 11:"Telegram", 14:"Splunk", 15:"Teams"}
                lines = ["📬 **Alert Contacts**\n"]
                for c in contacts:
                    lines.append(
                        f"📌 **{c.get('friendly_name', '?')}** — {CTYPE.get(c.get('type', 0), 'Other')}\n"
                        f"   `{c.get('value', '')}` | 🆔 `{c.get('id', '')}`\n"
                    )
                text = "\n".join(lines)
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Contact", callback_data="add_contact")],
                [InlineKeyboardButton("🔙 Menu",        callback_data="menu")],
            ])
            await safe_edit(query.message, text, reply_markup=markup)

        # ── Maintenance Windows ───────────────────────────────────────────────
        elif data in ("mwindow", "add_mwindow"):
            if data == "add_mwindow":
                _set_state(uid, "mw_name")
                markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
                await safe_edit(query.message,
                    "🪟 **New Maintenance Window**\n\nEnter a **name**:",
                    reply_markup=markup
                )
                return
            windows = await api.get_mwindows()
            if not windows:
                text = "🪟 No maintenance windows found."
            else:
                MW = {1:"Once", 2:"Daily", 3:"Weekly", 4:"Monthly"}
                lines = ["🪟 **Maintenance Windows**\n"]
                for w in windows:
                    lines.append(
                        f"🕐 **{w.get('friendly_name', '?')}** — {MW.get(w.get('type', 0), '?')}\n"
                        f"   ⏰ `{w.get('start_time', '?')}` • ⏱ `{w.get('duration', '?')}` min | 🆔 `{w.get('id', '')}`\n"
                    )
                text = "\n".join(lines)
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Window", callback_data="add_mwindow")],
                [InlineKeyboardButton("🔙 Menu",       callback_data="menu")],
            ])
            await safe_edit(query.message, text, reply_markup=markup)

        # ── PSP ───────────────────────────────────────────────────────────────
        elif data in ("psp", "add_psp"):
            if data == "add_psp":
                _set_state(uid, "psp_name")
                markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
                await safe_edit(query.message,
                    "📄 **New Status Page**\n\nEnter a **name**:",
                    reply_markup=markup
                )
                return
            psps = await api.get_psps()
            if not psps:
                text = "📄 No public status pages found."
            else:
                lines = ["📄 **Public Status Pages**\n"]
                for p in psps:
                    sd = p.get("custom_domain") or f"{p.get('subdomain', '?')}.uptimerobot.com"
                    lines.append(f"🌐 **{p.get('friendly_name', '?')}**\n   🔗 `{sd}` | 🆔 `{p.get('id', '')}`\n")
                text = "\n".join(lines)
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Page", callback_data="add_psp")],
                [InlineKeyboardButton("🔙 Menu",     callback_data="menu")],
            ])
            await safe_edit(query.message, text, reply_markup=markup)

        # ── Add monitor ───────────────────────────────────────────────────────
        elif data == "add_monitor":
            _set_state(uid, "add_name")
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            await safe_edit(query.message,
                "➕ **Add New Monitor**\n\n"
                "Step 1 of 3\n"
                "━━━━━━━━━━━━━━━\n"
                "Enter a **friendly name** for this monitor:\n"
                "_e.g. My Website, API Server_",
                reply_markup=markup
            )

        elif data.startswith("add_type_"):
            mtype = int(data.split("_")[-1])
            state = _get_state(uid)
            if not state or state.get("step") != "add_type":
                await safe_edit(query.message, "⚠️ Session expired. Use /add again.")
                return
            TYPE_LABELS = {1: "HTTP(s)", 2: "Keyword", 3: "Ping", 4: "Port"}
            mon_name = state["data"].get("name", "?")
            mon_url  = state["data"].get("url", "?")
            user_state.pop(uid, None)
            result = await api.new_monitor(mon_name, mon_url, mtype)
            if result:
                mid = result.get("monitor", {}).get("id", "?")
                await safe_edit(query.message,
                    f"✅ **Monitor created!**\n\n"
                    f"📛 Name: `{mon_name}`\n"
                    f"🔗 URL: `{mon_url}`\n"
                    f"🔧 Type: {TYPE_LABELS.get(mtype, '?')}\n"
                    f"🆔 ID: `{mid}`"
                )
            else:
                await safe_edit(query.message, "❌ Failed to create monitor. Check URL and try again.")

        elif data.startswith("ct_"):
            ctype = int(data.split("_")[-1])
            state = _get_state(uid)
            if not state or state.get("step") != "contact_type":
                await safe_edit(query.message, "⚠️ Session expired. Try again.")
                return
            state["data"]["type"] = ctype
            state["step"] = "contact_value"
            LABELS = {2: "email address", 3: "webhook URL", 9: "Slack webhook URL", 11: "Telegram chat ID"}
            label  = LABELS.get(ctype, "value")
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            await safe_edit(query.message,
                f"Enter the **{label}** for this contact:",
                reply_markup=markup
            )

        elif data.startswith("mw_type_"):
            mtype = int(data.split("_")[-1])
            state = _get_state(uid)
            if not state or state.get("step") != "mw_type":
                await safe_edit(query.message, "⚠️ Session expired. Try again.")
                return
            state["data"]["mw_type"] = mtype
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            if mtype == 3:
                state["step"] = "mw_value"
                state["data"]["mw_value_hint"] = "weekly"
                await safe_edit(query.message,
                    "Enter **day of week** (1 = Monday … 7 = Sunday):",
                    reply_markup=markup
                )
            elif mtype == 4:
                state["step"] = "mw_value"
                state["data"]["mw_value_hint"] = "monthly"
                await safe_edit(query.message,
                    "Enter **day of month** (1 – 28):",
                    reply_markup=markup
                )
            else:
                state["step"] = "mw_time"
                state["data"]["mw_value"] = ""
                await safe_edit(query.message,
                    "Enter **start time** in `HH:MM` format (UTC):\n(e.g. `02:00` for 2 AM UTC)",
                    reply_markup=markup
                )

        elif data == "psp_monitors_all":
            state = _get_state(uid)
            if not state or "name" not in state.get("data", {}):
                await safe_edit(query.message, "⚠️ Session expired. Try again.")
                return
            psp_name = state["data"]["name"]
            user_state.pop(uid, None)
            result = await api.new_psp(psp_name, monitors="0")
            if result:
                pid = result.get("psp", {}).get("id", "?")
                await safe_edit(query.message,
                    f"✅ **Status page created!**\n\n"
                    f"📛 Name: `{psp_name}`\n"
                    f"🆔 ID: `{pid}`"
                )
            else:
                await safe_edit(query.message, "❌ Failed to create status page.")

        elif data == "psp_monitors_custom":
            state = _get_state(uid)
            if not state or "name" not in state.get("data", {}):
                await safe_edit(query.message, "⚠️ Session expired. Try again.")
                return
            state["step"] = "psp_monitor_ids"
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            await safe_edit(query.message,
                "Enter **monitor IDs** separated by `-`:\n(e.g. `12345-67890`)\nGet IDs from /status",
                reply_markup=markup
            )

        elif data.startswith("confirm_delete_"):
            mid = data.replace("confirm_delete_", "")
            ok  = await api.delete_monitor(mid)
            await safe_edit(query.message,
                f"🗑️ Monitor `{mid}` deleted." if ok else f"❌ Failed to delete `{mid}`."
            )

        elif data.startswith("confirm_delcontact_"):
            cid = data.replace("confirm_delcontact_", "")
            ok  = await api.delete_alert_contact(cid)
            await safe_edit(query.message,
                f"🗑️ Contact `{cid}` deleted." if ok else f"❌ Failed to delete contact `{cid}`."
            )

        elif data.startswith("confirm_delmwindow_"):
            wid = data.replace("confirm_delmwindow_", "")
            ok  = await api.delete_mwindow(wid)
            await safe_edit(query.message,
                f"🗑️ Window `{wid}` deleted." if ok else f"❌ Failed to delete window `{wid}`."
            )

        elif data.startswith("confirm_delpsp_"):
            pid = data.replace("confirm_delpsp_", "")
            ok  = await api.delete_psp(pid)
            await safe_edit(query.message,
                f"🗑️ Status page `{pid}` deleted." if ok else f"❌ Failed to delete PSP `{pid}`."
            )
