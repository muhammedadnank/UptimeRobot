from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified
from utils import get_api_for
from db import delete_user
from handlers.monitors import build_status, build_stats, build_alerts, user_state, _set_state, _get_state

NO_KEY_MSG = "🔑 No API key set. Use /setkey to link your UptimeRobot account."


async def safe_edit(message, text, reply_markup=None):
    """Edit a message, silently ignoring MessageNotModified errors (e.g. from double-taps)."""
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except MessageNotModified:
        pass


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Status",      callback_data="status"),
            InlineKeyboardButton("📈 Stats",        callback_data="stats"),
            InlineKeyboardButton("🔔 Alerts",       callback_data="alerts"),
        ],
        [
            InlineKeyboardButton("👤 Account",      callback_data="account"),
            InlineKeyboardButton("📬 Contacts",     callback_data="contacts"),
            InlineKeyboardButton("🪟 MWindows",     callback_data="mwindow"),
        ],
        [
            InlineKeyboardButton("📄 PSP",          callback_data="psp"),
            InlineKeyboardButton("➕ Add Monitor",  callback_data="add_monitor"),
        ],
    ])


def register(app: Client):

    @app.on_callback_query()
    async def on_callback(client: Client, query: CallbackQuery):
        await query.answer()
        data = query.data
        uid  = query.from_user.id
        api  = await get_api_for(uid)

        # Commands that don't need API key
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
            await safe_edit(query.message, 
                "🖥️ **UptimeRobot Control Panel**\nChoose an action:",
                reply_markup=main_keyboard()
            )
            return

        # All remaining callbacks need API key
        if not api:
            await safe_edit(query.message, NO_KEY_MSG)
            return

        # ── Monitor views ─────────────────────────────────────────────────────
        if data == "status":
            text, markup = await build_status(api)
            await safe_edit(query.message, text, reply_markup=markup)

        elif data == "stats":
            text, markup = await build_stats(api)
            await safe_edit(query.message, text, reply_markup=markup)

        elif data == "alerts":
            text, markup = await build_alerts(api)
            await safe_edit(query.message, text, reply_markup=markup)

        # ── Account ───────────────────────────────────────────────────────────
        elif data == "account":
            acc = await api.get_account_details()
            if not acc:
                await safe_edit(query.message, "❌ Could not fetch account details.")
                return
            used = acc.get("up_monitors", 0) + acc.get("down_monitors", 0) + acc.get("paused_monitors", 0)
            text = (
                "👤 **Account Details**\n\n"
                f"📧 Email: `{acc.get('email', '?')}`\n"
                f"📊 Monitors: `{used}` / `{acc.get('monitor_limit', '?')}`\n"
                f"⏱ Interval: every `{acc.get('monitor_interval', '?')}` min\n\n"
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
                "➕ **Add New Monitor**\n\nStep 1/3 — Enter a **friendly name**:",
                reply_markup=markup
            )

        # ── Add monitor type ──────────────────────────────────────────────────
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

        # ── Contact type ──────────────────────────────────────────────────────
        elif data.startswith("ct_"):
            ctype = int(data.split("_")[-1])
            state = _get_state(uid)
            if not state or state.get("step") != "contact_type":
                await safe_edit(query.message, "⚠️ Session expired. Try again.")
                return
            state["data"]["type"] = ctype
            state["step"] = "contact_value"
            LABELS = {1: "phone number", 2: "email address", 3: "webhook URL", 9: "Slack URL", 11: "chat ID"}
            label  = LABELS.get(ctype, "value")
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            await safe_edit(query.message, 
                f"Enter the **{label}** for this contact:",
                reply_markup=markup
            )

        # ── Maintenance window type ───────────────────────────────────────────
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

        # ── PSP monitor selection ─────────────────────────────────────────────
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
                await safe_edit(query.message, f"✅ Status page created!\nID: `{pid}`")
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

        # ── Confirm deletions ─────────────────────────────────────────────────
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
