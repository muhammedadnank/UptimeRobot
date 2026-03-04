# 🤖 UptimeRobot Telegram Bot

Full control of your UptimeRobot account directly from Telegram. Built with **Pyrogram** (MTProto) and **aiohttp**.

---

## ✨ Features

### 🖥️ Monitors
- View all monitor statuses (Up / Down / Paused)
- Response time & uptime % stats (7d / 30d / 90d)
- Add new monitors (HTTP, Keyword, Ping, Port)
- Pause / Resume / Delete monitors

### 👤 Account
- View account email, monitor limit, and check interval
- Up / Down / Paused monitor counts

### 🔔 Alert Contacts
- List all alert contacts
- Add new contacts (Email, Telegram, Webhook, SMS, Slack)
- Delete contacts

### 🪟 Maintenance Windows
- List maintenance windows
- Create new windows (Once / Daily / Weekly / Monthly)
- Delete windows

### 📄 Public Status Pages
- List status pages
- Create new status pages
- Delete status pages

### 🔒 Security
- Restrict bot access via `ALLOWED_USERS`
- Confirmation prompt before all delete operations

---

## 📋 Commands

| Command | Description |
|---------|-------------|
| `/start` | Help message & command list |
| `/menu` | Interactive button panel |
| **Monitors** | |
| `/status` | Status of all monitors |
| `/stats` | Uptime % & response times |
| `/alerts` | Recent alert logs |
| `/add` | Add a new monitor (guided) |
| `/pause <id>` | Pause a monitor |
| `/resume <id>` | Resume a monitor |
| `/delete <id>` | Delete a monitor |
| **Account** | |
| `/account` | Account details |
| **Alert Contacts** | |
| `/contacts` | List alert contacts |
| `/addcontact` | Add a new contact (guided) |
| `/delcontact <id>` | Delete a contact |
| **Maintenance Windows** | |
| `/mwindow` | List maintenance windows |
| `/addmwindow` | Add a new window (guided) |
| `/delmwindow <id>` | Delete a window |
| **Status Pages** | |
| `/psp` | List public status pages |
| `/addpsp` | Add a new status page (guided) |
| `/delpsp <id>` | Delete a status page |

---

## 📁 Project Structure

```
uptimebot/
├── bot.py                  # Main entry point, /start and /menu handlers
├── uptime_robot.py         # Async UptimeRobot API wrapper (aiohttp)
├── utils.py                # Auth helpers & shared API instance
├── requirements.txt        # Python dependencies
├── Procfile                # Process config (Railway / Render)
├── railway.toml            # Railway deployment config
├── .env.example            # Environment variable template
└── handlers/
    ├── __init__.py
    ├── monitors.py         # Monitor commands + multi-step state machine
    ├── account.py          # /account command
    ├── contacts.py         # Alert contact commands
    ├── mwindow.py          # Maintenance window commands
    ├── psp.py              # Public status page commands
    └── callbacks.py        # All inline keyboard button handlers
```

---

## 🔧 Setup

### Step 1 — Get Credentials

| Variable | Where to get it |
|----------|----------------|
| `API_ID` | [my.telegram.org](https://my.telegram.org) → API Development Tools |
| `API_HASH` | [my.telegram.org](https://my.telegram.org) → API Development Tools |
| `BOT_TOKEN` | Telegram → `@BotFather` → `/newbot` |
| `UPTIMEROBOT_API_KEY` | [UptimeRobot Dashboard](https://dashboard.uptimerobot.com) → My Settings → API Settings → Main API Key |
| `ALLOWED_USERS` | Telegram → `@userinfobot` → your user ID *(optional)* |

### Step 2 — Local Testing

```bash
# Install dependencies
pip install kurigram aiohttp

# Setup environment
cp .env.example .env
# Fill in your values in the .env file

# Run
python bot.py
```

---

## ☁️ Deploy — Railway

1. **Push to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/uptimebot.git
git push -u origin main
```

2. **Deploy on Railway:**
   - Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
   - Select your repository
   - In the **Variables** tab, add:
     ```
     API_ID              = 12345678
     API_HASH            = your_api_hash
     BOT_TOKEN           = your_bot_token
     UPTIMEROBOT_API_KEY = ur_your_key
     ALLOWED_USERS       = 123456789   (optional)
     ```
   - Auto deploy! ✅

---

## ☁️ Deploy — Render

1. Push to GitHub (same as above)
2. Go to [render.com](https://render.com) → **New** → **Background Worker**
3. Connect your repository
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. Add environment variables (same as Railway)
6. Click **Create Background Worker** → Deploy! ✅

---

## ⚙️ Environment Variables

```env
# Telegram MTProto credentials (from my.telegram.org)
API_ID=12345678
API_HASH=your_api_hash_here

# Bot token (from @BotFather)
BOT_TOKEN=your_bot_token_here

# UptimeRobot Main API Key
UPTIMEROBOT_API_KEY=ur_your_key_here

# Optional: Comma-separated Telegram user IDs allowed to use the bot
# Leave empty to allow everyone
ALLOWED_USERS=123456789,987654321
```

---

## 🛠️ Tech Stack

| Package | Purpose |
|---------|---------|
| `kurigram` | Telegram MTProto bot framework (Pyrogram fork — imports as `pyrogram`) |
| `aiohttp` | Async HTTP client for UptimeRobot API calls |

---

## 📝 Notes

- Bot supports **private chats only** — it does not work in groups
- For multi-step flows (`/add`, `/addcontact`, `/addmwindow`, `/addpsp`), use the **❌ Cancel** button to abort
- UptimeRobot Free plan has a 10 API requests/minute rate limit
- Use `/status` to find monitor IDs for pause/resume/delete commands

---

## 🐛 Code Review — Issues Found

The following bugs and improvements were identified during a full review of the codebase:

### 🟡 Bug — `CallbackQuery` import unused in `contacts.py`

**File:** `handlers/contacts.py`, line 2

`CallbackQuery` is imported but never used in that file. Contact callback handling is done in `callbacks.py`.

**Fix:**
```python
# Remove CallbackQuery from import
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
```

---

### 🟡 Bug — `user_state` not cleared on `/add` URL validation failure

**File:** `handlers/monitors.py` — `handle_text()`, step `add_url`

When the user enters an invalid URL (not starting with `http`), the function returns early with a warning message — but the state is not changed, so the user can re-enter. This is actually correct behaviour. However, there is no timeout or cleanup mechanism for abandoned sessions. If a user starts `/add` and never finishes, their state entry leaks forever in `user_state`.

**Recommended fix:** Add a periodic cleanup task or a per-user TTL:
```python
import time
# Store state with timestamp: user_state[uid] = {"step": ..., "data": ..., "ts": time.time()}
# Periodically clean up entries older than e.g. 10 minutes
```

---

### 🟡 Bug — `mw_value` field never set for non-Once maintenance windows

**File:** `handlers/monitors.py` — state machine for `mw_type_` callback

After the user selects a window type (Daily / Weekly / Monthly), the state jumps directly to `mw_time`. But the UptimeRobot API requires a `value` field for Weekly (day-of-week) and Monthly (day-of-month) windows. The `value` defaults to `""` (empty string), which will likely cause API errors for those types.

**Fix:** After choosing Weekly or Monthly, add an extra step to collect the value:
```python
# For Weekly: ask "Enter day of week (1=Mon ... 7=Sun):"
# For Monthly: ask "Enter day of month (1–28):"
```

---

### 🟡 Bug — `PSP_SORT` dict defined but never used

**File:** `handlers/psp.py`, line 4

```python
PSP_SORT = {1:"Friendly Name A-Z", 2:"Friendly Name Z-A", ...}
```

This dict is never referenced anywhere. Either use it or remove it.

---

### 🟡 Minor — Inconsistent "Back to Menu" buttons

Some callback views (e.g. `status`, `stats`, `alerts`) have no **🔙 Menu** button, while others (e.g. `account`, `contacts`) do. This makes navigation inconsistent.

**Fix:** Add a back button to the status/stats/alerts inline keyboards:
```python
markup = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🔄 Refresh", callback_data="status"),
        InlineKeyboardButton("📈 Stats",   callback_data="stats"),
        InlineKeyboardButton("🔔 Alerts",  callback_data="alerts"),
    ],
    [InlineKeyboardButton("🔙 Menu", callback_data="menu")],  # ← add this
])
```

---

### 🟡 Minor — `/alerts` and `/stats` have no back/refresh buttons (command version)

`build_stats()` and `build_alerts()` return plain strings with no inline markup. When called from the callback handler these get edited into messages with no buttons, leaving the user stuck without navigation. The `build_status()` function correctly returns markup — the others should too.

---

### 🟢 Suggestion — Pin package versions in requirements.txt

```
kurigram==<latest>
aiohttp==3.10.5
```

Unpinned packages can break on new major versions.

---

### 🟢 Suggestion — Add `/cancel` as a proper command handler

Currently, cancel is only reachable via an inline button. Users who type `/cancel` in a multi-step flow get no response (the command is not in the exclusion list of `handle_text`, but there is no `/cancel` command handler registered). Add:

```python
@app.on_message(filters.command("cancel") & filters.private)
async def cmd_cancel(client, message):
    user_state.pop(message.from_user.id, None)
    await message.reply("❌ Operation cancelled.", quote=True)
```

And add `"cancel"` to the exclusion list in the text handler filter.

---
