# 🤖 UptimeRobot Telegram Bot

Telegram വഴി നിങ്ങളുടെ UptimeRobot account പൂർണ്ണമായും control ചെയ്യാൻ കഴിയുന്ന bot. **Kurigram** (Pyrogram fork) ഉപയോഗിച്ച് നിർമ്മിച്ചത്.

---

## ✨ Features

### 🖥️ Monitors
- എല്ലാ monitors-ന്റെയും status (Up / Down / Paused) കാണാം
- Response time & uptime % (7d / 30d / 90d) stats
- പുതിയ monitor add ചെയ്യാം (HTTP, Keyword, Ping, Port)
- Monitor pause / resume / delete

### 👤 Account
- Account email, monitor limit, interval കാണാം
- Up / Down / Paused monitor counts

### 🔔 Alert Contacts
- എല്ലാ alert contacts-ഉം list ചെയ്യാം
- പുതിയ contact add ചെയ്യാം (Email, Telegram, Webhook, SMS, Slack)
- Contact delete ചെയ്യാം

### 🪟 Maintenance Windows
- Maintenance windows list കാണാം
- പുതിയ window create ചെയ്യാം (Once / Daily / Weekly / Monthly)
- Window delete ചെയ്യാം

### 📄 Public Status Pages
- Status pages list കാണാം
- പുതിയ status page create ചെയ്യാം
- Status page delete ചെയ്യാം

### 🔒 Security
- `ALLOWED_USERS` വഴി bot access restrict ചെയ്യാം
- Delete operations-ന് confirmation prompt

---

## 📋 Commands

| Command | Description |
|---------|-------------|
| `/start` | Help message & command list |
| `/menu` | Interactive button panel |
| **Monitors** | |
| `/status` | എല്ലാ monitors-ന്റെ status |
| `/stats` | Uptime % & response times |
| `/alerts` | Recent alert logs |
| `/add` | പുതിയ monitor add (guided) |
| `/pause <id>` | Monitor pause ചെയ്യുക |
| `/resume <id>` | Monitor resume ചെയ്യുക |
| `/delete <id>` | Monitor delete ചെയ്യുക |
| **Account** | |
| `/account` | Account details |
| **Alert Contacts** | |
| `/contacts` | Alert contacts list |
| `/addcontact` | പുതിയ contact add (guided) |
| `/delcontact <id>` | Contact delete ചെയ്യുക |
| **Maintenance Windows** | |
| `/mwindow` | Maintenance windows list |
| `/addmwindow` | പുതിയ window add (guided) |
| `/delmwindow <id>` | Window delete ചെയ്യുക |
| **Status Pages** | |
| `/psp` | Public status pages list |
| `/addpsp` | പുതിയ status page add (guided) |
| `/delpsp <id>` | Status page delete ചെയ്യുക |

---

## 📁 Project Structure

```
uptimebot/
├── bot.py                  # Main entry point
├── uptime_robot.py         # UptimeRobot API wrapper (async/aiohttp)
├── utils.py                # Auth helpers & shared API instance
├── requirements.txt        # Python dependencies
├── Procfile                # Process config (Railway/Render)
├── railway.toml            # Railway deployment config
├── .env.example            # Environment variable template
└── handlers/
    ├── __init__.py
    ├── monitors.py         # Monitor commands + multi-step state machine
    ├── account.py          # Account command
    ├── contacts.py         # Alert contact commands
    ├── mwindow.py          # Maintenance window commands
    ├── psp.py              # Public status page commands
    └── callbacks.py        # All inline button handlers
```

---

## 🔧 Setup

### Step 1 — Credentials നേടുക

| Variable | എവിടെ നിന്ന് |
|----------|--------------|
| `API_ID` | [my.telegram.org](https://my.telegram.org) → API Development Tools |
| `API_HASH` | [my.telegram.org](https://my.telegram.org) → API Development Tools |
| `BOT_TOKEN` | Telegram → `@BotFather` → `/newbot` |
| `UPTIMEROBOT_API_KEY` | [UptimeRobot Dashboard](https://dashboard.uptimerobot.com) → My Settings → API Settings → Main API Key |
| `ALLOWED_USERS` | Telegram → `@userinfobot` → നിങ്ങളുടെ user ID *(optional)* |

### Step 2 — Local Testing

```bash
# Install dependencies
pip install kurigram aiohttp

# Setup environment
cp .env.example .env
# .env file-ൽ values fill ചെയ്യുക

# Run
python bot.py
```

---

## ☁️ Deploy — Railway

1. **GitHub-ൽ push ചെയ്യുക:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/uptimebot.git
git push -u origin main
```

2. **Railway-ൽ deploy:**
   - [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
   - Repository select ചെയ്യുക
   - **Variables** tab → Add environment variables:
     ```
     API_ID          = 12345678
     API_HASH        = your_api_hash
     BOT_TOKEN       = your_bot_token
     UPTIMEROBOT_API_KEY = ur_your_key
     ALLOWED_USERS   = 123456789   (optional)
     ```
   - Auto deploy! ✅

---

## ☁️ Deploy — Render

1. GitHub-ൽ push ചെയ്യുക (same as above)
2. [render.com](https://render.com) → **New** → **Background Worker**
3. Repository connect ചെയ്യുക
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. Environment Variables add ചെയ്യുക (same as Railway)
6. **Create Background Worker** → Deploy! ✅

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
| `kurigram` | Telegram MTProto bot framework (Pyrogram fork) |
| `aiohttp` | Async HTTP client for UptimeRobot API calls |

---

## 📝 Notes

- Bot **private chats** മാത്രം support ചെയ്യുന്നു (groups-ൽ work ചെയ്യില്ല)
- Multi-step flows (/add, /addcontact, /addmwindow, /addpsp) cancel ചെയ്യാൻ `/cancel` button ഉപയോഗിക്കുക
- UptimeRobot Free plan: 10 API requests/minute rate limit ഉണ്ട്
- Monitor IDs കാണാൻ `/status` command use ചെയ്യുക
