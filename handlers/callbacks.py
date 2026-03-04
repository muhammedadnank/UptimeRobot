from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils import is_authorized, get_api
from handlers.monitors import build_status, build_stats, build_alerts, user_state


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Status",   callback_data="status"),
            InlineKeyboardButton("📈 Stats",    callback_data="stats"),
            InlineKeyboardButton("🔔 Alerts",   callback_data="alerts"),
        ],
        [
            InlineKeyboardButton("👤 Account",  callback_data="account"),
            InlineKeyboardButton("📬 Contacts", callback_data="contacts"),
            InlineKeyboardButton("🪟 MWindows", callback_data="mwindow"),
        ],
        [
            InlineKeyboardButton("📄 PSP",      callback_data="psp"),
            InlineKeyboardButton("➕ Add Monitor", callback_data="add_monitor"),
        ],
    ])


def register(app: Client):

    @app.on_callback_query()
    async def on_callback(client: Client, query: CallbackQuery):
        if not is_authorized(query.from_user.id):
            await query.answer("⛔ Access Denied", show_alert=True)
            return

        await query.answer()
        data = query.data
        uid  = query.from_user.id
        api  = get_api()

        # ── Menu ──────────────────────────────────────────────────────────────
        if data == "menu":
            await query.message.edit_text(
                "🖥️ **UptimeRobot Control Panel**\nChoose an action:",
                reply_markup=main_keyboard()
            )

        # ── Monitor views ─────────────────────────────────────────────────────
        elif data == "status":
            text, markup = await build_status(api)
            await query.message.edit_text(text, reply_markup=markup)

        elif data == "stats":
            await query.message.edit_text(await build_stats(api))

        elif data == "alerts":
            await query.message.edit_text(await build_alerts(api))

        # ── Account ───────────────────────────────────────────────────────────
        elif data == "account":
            acc = await api.get_account_details()
            if not acc:
                await query.message.edit_text("❌ Could not fetch account details.")
                return
            used  = acc.get("up_monitors",0) + acc.get("down_monitors",0) + acc.get("paused_monitors",0)
            text  = (
                "👤 **Account Details**\n\n"
                f"📧 Email: `{acc.get('email','?')}`\n"
                f"📊 Monitors: `{used}` / `{acc.get('monitor_limit','?')}`\n"
                f"⏱ Interval: every `{acc.get('monitor_interval','?')}` min\n\n"
                f"✅ Up: `{acc.get('up_monitors',0)}`  "
                f"🔴 Down: `{acc.get('down_monitors',0)}`  "
                f"⏸️ Paused: `{acc.get('paused_monitors',0)}`"
            )
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="menu")]])
            await query.message.edit_text(text, reply_markup=markup)

        # ── Contacts ──────────────────────────────────────────────────────────
        elif data in ("contacts", "add_contact"):
            if data == "add_contact":
                user_state[uid] = {"step": "contact_name", "data": {}}
                markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
                await query.message.edit_text(
                    "➕ **Add Alert Contact**\n\nEnter a **friendly name**:",
                    reply_markup=markup
                )
                return
            contacts = await api.get_alert_contacts()
            if not contacts:
                text = "📭 No alert contacts found."
            else:
                CTYPE = {1:"SMS",2:"Email",3:"Webhook",9:"Slack",11:"Telegram",14:"Splunk",15:"Teams"}
                lines = ["📬 **Alert Contacts**\n"]
                for c in contacts:
                    lines.append(
                        f"📌 **{c.get('friendly_name','?')}** — {CTYPE.get(c.get('type',0), 'Other')}\n"
                        f"   `{c.get('value','')}` | 🆔 `{c.get('id','')}`\n"
                    )
                text = "\n".join(lines)
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Contact", callback_data="add_contact")],
                [InlineKeyboardButton("🔙 Menu",        callback_data="menu")],
            ])
            await query.message.edit_text(text, reply_markup=markup)

        # ── Maintenance Windows ───────────────────────────────────────────────
        elif data in ("mwindow", "add_mwindow"):
            if data == "add_mwindow":
                user_state[uid] = {"step": "mw_name", "data": {}}
                markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
                await query.message.edit_text(
                    "🪟 **New Maintenance Window**\n\nEnter a **name**:",
                    reply_markup=markup
                )
                return
            windows = await api.get_mwindows()
            if not windows:
                text = "🪟 No maintenance windows found."
            else:
                MW = {1:"Once",2:"Daily",3:"Weekly",4:"Monthly"}
                lines = ["🪟 **Maintenance Windows**\n"]
                for w in windows:
                    lines.append(
                        f"🕐 **{w.get('friendly_name','?')}** — {MW.get(w.get('type',0),'?')}\n"
                        f"   ⏰ `{w.get('start_time','?')}` • ⏱ `{w.get('duration','?')}` min | 🆔 `{w.get('id','')}`\n"
                    )
                text = "\n".join(lines)
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Window", callback_data="add_mwindow")],
                [InlineKeyboardButton("🔙 Menu",       callback_data="menu")],
            ])
            await query.message.edit_text(text, reply_markup=markup)

        # ── PSP ───────────────────────────────────────────────────────────────
        elif data in ("psp", "add_psp"):
            if data == "add_psp":
                user_state[uid] = {"step": "psp_name", "data": {}}
                markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
                await query.message.edit_text(
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
                    sd = p.get("custom_domain") or f"{p.get('subdomain','?')}.uptimerobot.com"
                    lines.append(f"🌐 **{p.get('friendly_name','?')}**\n   🔗 `{sd}` | 🆔 `{p.get('id','')}`\n")
                text = "\n".join(lines)
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Page", callback_data="add_psp")],
                [InlineKeyboardButton("🔙 Menu",     callback_data="menu")],
            ])
            await query.message.edit_text(text, reply_markup=markup)

        # ── Add monitor ───────────────────────────────────────────────────────
        elif data == "add_monitor":
            user_state[uid] = {"step": "add_name", "data": {}}
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            await query.message.edit_text(
                "➕ **Add New Monitor**\n\nStep 1/3 — Enter a **friendly name**:",
                reply_markup=markup
            )

        # ── Add monitor: type selection ───────────────────────────────────────
        elif data.startswith("add_type_"):
            mtype = int(data.split("_")[-1])
            state = user_state.get(uid)
            if not state or state.get("step") != "add_type":
                await query.message.edit_text("⚠️ Session expired. Use /add again.")
                return
            TYPE_LABELS = {1:"HTTP(s)", 2:"Keyword", 3:"Ping", 4:"Port"}
            mon_name = state["data"].get("name", "?")
            mon_url  = state["data"].get("url", "?")
            user_state.pop(uid, None)
            result = await api.new_monitor(mon_name, mon_url, mtype)
            if result:
                mid = result.get("monitor", {}).get("id", "?")
                await query.message.edit_text(
                    f"✅ **Monitor created!**\n\n"
                    f"📛 Name: `{mon_name}`\n"
                    f"🔗 URL: `{mon_url}`\n"
                    f"🔧 Type: {TYPE_LABELS.get(mtype,'?')}\n"
                    f"🆔 ID: `{mid}`"
                )
            else:
                await query.message.edit_text("❌ Failed to create monitor. Check URL and try again.")

        # ── Contact type selection ────────────────────────────────────────────
        elif data.startswith("ct_"):
            ctype = int(data.split("_")[-1])
            state = user_state.get(uid)
            if not state or state.get("step") != "contact_type":
                await query.message.edit_text("⚠️ Session expired. Try again.")
                return
            state["data"]["type"] = ctype
            state["step"] = "contact_value"
            LABELS = {1:"phone number", 2:"email address", 3:"webhook URL", 9:"Slack URL", 11:"chat ID"}
            label  = LABELS.get(ctype, "value")
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            await query.message.edit_text(
                f"Enter the **{label}** for this contact:",
                reply_markup=markup
            )

        elif data.startswith("mw_type_"):
            mtype = int(data.split("_")[-1])
            state = user_state.get(uid)
            if not state or state.get("step") != "mw_type":
                await query.message.edit_text("⚠️ Session expired. Try again.")
                return
            state["data"]["mw_type"] = mtype
            state["step"] = "mw_time"
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            await query.message.edit_text(
                "Enter **start time** in `HH:MM` format (UTC):\n(e.g. `02:00` for 2 AM UTC)",
                reply_markup=markup
            )

        # ── PSP: monitor selection ────────────────────────────────────────────
        elif data == "psp_monitors_all":
            state = user_state.get(uid)
            if not state or "name" not in state.get("data", {}):
                await query.message.edit_text("⚠️ Session expired. Try again.")
                return
            psp_name = state["data"]["name"]
            user_state.pop(uid, None)
            result = await api.new_psp(psp_name, monitors="0")
            if result:
                pid = result.get("psp", {}).get("id", "?")
                await query.message.edit_text(f"✅ Status page created!\nID: `{pid}`")
            else:
                await query.message.edit_text("❌ Failed to create status page.")

        elif data == "psp_monitors_custom":
            state = user_state.get(uid)
            if not state or "name" not in state.get("data", {}):
                await query.message.edit_text("⚠️ Session expired. Try again.")
                return
            state["step"] = "psp_monitor_ids"
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
            await query.message.edit_text(
                "Enter **monitor IDs** separated by `-`:\n(e.g. `12345-67890`)\nGet IDs from /status",
                reply_markup=markup
            )

        # ── Confirm deletions ─────────────────────────────────────────────────
        elif data.startswith("confirm_delete_"):
            mid = data.replace("confirm_delete_", "")
            ok  = await api.delete_monitor(mid)
            await query.message.edit_text(
                f"🗑️ Monitor `{mid}` deleted." if ok else f"❌ Failed to delete `{mid}`."
            )

        elif data.startswith("confirm_delcontact_"):
            cid = data.replace("confirm_delcontact_", "")
            ok  = await api.delete_alert_contact(cid)
            await query.message.edit_text(
                f"🗑️ Contact `{cid}` deleted." if ok else f"❌ Failed to delete contact `{cid}`."
            )

        elif data.startswith("confirm_delmwindow_"):
            wid = data.replace("confirm_delmwindow_", "")
            ok  = await api.delete_mwindow(wid)
            await query.message.edit_text(
                f"🗑️ Window `{wid}` deleted." if ok else f"❌ Failed to delete window `{wid}`."
            )

        elif data.startswith("confirm_delpsp_"):
            pid = data.replace("confirm_delpsp_", "")
            ok  = await api.delete_psp(pid)
            await query.message.edit_text(
                f"🗑️ Status page `{pid}` deleted." if ok else f"❌ Failed to delete PSP `{pid}`."
            )

        # ── Cancel ────────────────────────────────────────────────────────────
        elif data == "cancel":
            user_state.pop(uid, None)
            await query.message.edit_text("❌ Operation cancelled.", reply_markup=None)
