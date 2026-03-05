<div align="center">

# 🤖 UptimeRobot Telegram Bot

**Full control of your UptimeRobot account — directly from Telegram.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![Pyrogram](https://img.shields.io/badge/Pyrogram-kurigram-2ca5e0?logo=telegram&logoColor=white)](https://github.com/KurimuzonAkuma/pyrogram)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47a248?logo=mongodb&logoColor=white)](https://cloud.mongodb.com)
[![Deploy on Railway](https://img.shields.io/badge/Deploy-Railway-6441a5?logo=railway&logoColor=white)](https://railway.app)
[![Deploy on Render](https://img.shields.io/badge/Deploy-Render-46e3b7?logo=render&logoColor=white)](https://render.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## ✨ Features

| Category | Capabilities |
|---|---|
| 🔑 **Auth** | Each user links their own UptimeRobot API key — securely stored per-user in MongoDB |
| 🖥️ **Monitors** | View Up/Down/Paused status, uptime % (7d / 30d / 90d), response times, add / pause / resume / delete |
| 👤 **Account** | Email, monitor limit, check interval, counts by status |
| 🔔 **Alert Contacts** | List, add (Email / Telegram / Webhook / Slack), delete |
| 🪟 **Maintenance Windows** | List, create (Once / Daily / Weekly / Monthly), delete |
| 📄 **Public Status Pages** | List, create, delete |
| 🔍 **Inline Search** | Type `@bot <query>` in any chat to instantly share monitor status |
| 🔒 **Security** | Per-user API key isolation, confirmation prompt on all destructive actions, ban system |
| 🌐 **Multi-user** | Unlimited users, each with their own UptimeRobot account |
| 👮 **Admin Panel** | Broadcast, ban/unban, detailed bot stats, force-subscribe, restart |

---

## 📋 Command Reference

### 🔑 Key Management
| Command | Description |
|---|---|
| `/setkey <api_key>` | Link your UptimeRobot API key |
| `/mykey` | Check whether an API key is currently set |
| `/deletekey` | Remove your stored API key |

### 🖥️ Monitors
| Command | Description |
|---|---|
| `/status` | Live status of all monitors |
| `/stats` | Uptime % and average response times |
| `/alerts` | Last 3 alert events per monitor |
| `/add` | Guided 3-step monitor creation |
| `/pause <id>` | Pause a monitor |
| `/resume <id>` | Resume a paused monitor |
| `/delete <id>` | Delete a monitor (confirmation required) |

### 👤 Account & Contacts
| Command | Description |
|---|---|
| `/account` | View account details |
| `/contacts` | List all alert contacts |
| `/addcontact` | Add a new contact (guided) |
| `/delcontact <id>` | Delete a contact |

### 🪟 Maintenance & Status Pages
| Command | Description |
|---|---|
| `/mwindow` | List maintenance windows |
| `/addmwindow` | Create a new maintenance window |
| `/delmwindow <id>` | Delete a maintenance window |
| `/psp` | List public status pages |
| `/addpsp` | Create a new status page |
| `/delpsp <id>` | Delete a status page |

### 🔧 General
| Command | Description |
|---|---|
| `/start` | Help message and full command list |
| `/menu` | Interactive inline button panel |
| `/cancel` | Cancel any in-progress multi-step operation |

### 👮 Admin Only
| Command | Description |
|---|---|
| `/botstats` | Users count, memory, uptime, force-sub status |
| `/broadcast` | Reply to any message with this to send it to all users |
| `/ban <id> [reason]` | Ban a user from using the bot |
| `/unban <id>` | Unban a user |
| `/bannedlist` | List all banned users |
| `/setfsub <@channel>` | Enable force-subscribe for a channel |
| `/delfsub` | Disable force-subscribe |
| `/restart` | Restart the bot process |

> 💡 Use `/status` to find monitor IDs needed for pause / resume / delete.  
> 👮 Admin commands only work for user IDs listed in the `ADMINS` env variable.

---

## 🔍 Inline Search

Type `@yourbotusername` in **any Telegram chat** to search your monitors without opening the bot.

| Query | Result |
|---|---|
| `@bot` | Overview + all monitors |
| `@bot mysite` | Search by name or URL |
| `@bot down` | Only down monitors |
| `@bot up` | Only up monitors |
| `@bot paused` | Only paused monitors |

Each result shows monitor name, status, URL, uptime %, response time, and ID.  
Tap a result to share it directly into the chat.

> ⚠️ **Enable inline mode first:** BotFather → your bot → **Bot Settings → Inline Mode → Enable**

---

## 📁 Project Structure

```
UptimeRobot-main/
│
├── bot.py                  # Entry point — Client setup, core handlers (/start /setkey /menu)
├── db.py                   # MongoDB — users, ban/unban, force-sub config
├── utils.py                # Per-user API instance cache (get_api_for)
├── uptime_robot.py         # UptimeRobot API wrapper (aiohttp, session reuse)
│
├── handlers/
│   ├── __init__.py
│   ├── middleware.py       # check_banned, check_force_sub, check_all
│   ├── monitors.py         # /status /stats /alerts /add /pause /resume /delete
│   ├── account.py          # /account
│   ├── contacts.py         # /contacts /addcontact /delcontact
│   ├── mwindow.py          # /mwindow /addmwindow /delmwindow
│   ├── psp.py              # /psp /addpsp /delpsp
│   ├── callbacks.py        # All inline keyboard callbacks + main_keyboard()
│   ├── admin.py            # /broadcast /ban /unban /bannedlist /botstats /restart /setfsub /delfsub
│   └── inline.py           # Inline mode — @bot <query> monitor search
│
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
├── Procfile                # worker: python bot.py
└── railway.toml            # Railway deployment config
```

---

## 🚀 Getting Started

### Step 1 — Gather Credentials

| Variable | Where to get it |
|---|---|
| `API_ID` | [my.telegram.org](https://my.telegram.org) → API Development Tools |
| `API_HASH` | [my.telegram.org](https://my.telegram.org) → API Development Tools |
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `MONGODB_URI` | [cloud.mongodb.com](https://cloud.mongodb.com) → Free Cluster → Connect → Drivers |
| `ADMINS` | Your Telegram user ID — get it from [@userinfobot](https://t.me/userinfobot) |
| `PORT` | Set to `10000` on Render, or any free port locally |

> Each user's UptimeRobot API key is stored in MongoDB — it is **not** an env variable.

---

### Step 2 — MongoDB Atlas (Free Tier)

1. Sign up at [cloud.mongodb.com](https://cloud.mongodb.com)
2. Create a free **M0** cluster
3. **Database Access** → add a user with a password
4. **Network Access** → allow `0.0.0.0/0`
5. **Connect → Drivers** → copy your connection string:
   ```
   mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

---

### Step 3 — Install & Run Locally

```bash
# Clone
git clone https://github.com/muhammedadnank/UptimeRobot.git
cd UptimeRobot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — fill in API_ID, API_HASH, BOT_TOKEN, MONGODB_URI, ADMINS, PORT

# Start
python bot.py
```

---

## ☁️ Deployment

### Railway

1. Push your code to GitHub
2. [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
3. Select your repo
4. **Variables** tab → add all env vars
5. Done — Railway auto-deploys on every push ✅

### Render

1. [render.com](https://render.com) → **New → Background Worker**
2. Connect your GitHub repo
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
4. Add all environment variables (set `PORT=10000`)
5. **Create Background Worker** → Deploy ✅

---

## ⚙️ Environment Variables

```env
# Telegram MTProto credentials — my.telegram.org
API_ID=12345678
API_HASH=your_api_hash_here

# Bot token — @BotFather
BOT_TOKEN=your_bot_token_here

# MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority

# Admin user IDs — space or comma separated
# Get your ID from @userinfobot on Telegram
ADMINS=123456789

# HTTP port for health check (Render uses 10000 by default)
PORT=10000
```

---

## 🛠️ Tech Stack

| Package | Purpose |
|---|---|
| [`kurigram`](https://github.com/KurimuzonAkuma/pyrogram) | Telegram MTProto — actively maintained Pyrogram fork |
| [`motor`](https://motor.readthedocs.io) | Async MongoDB driver |
| [`aiohttp`](https://docs.aiohttp.org) | Async HTTP client for UptimeRobot API |
| [`tgcrypto`](https://github.com/pyrogram/tgcrypto) | Fast Telegram encryption (speeds up MTProto) |
| [`psutil`](https://psutil.readthedocs.io) | System stats for `/botstats` (memory, uptime) |

---

## 🗄️ Database Schema

**Collection: `users`**

| Field | Type | Description |
|---|---|---|
| `telegram_id` | `int` | Unique index — Telegram user ID |
| `api_key` | `str` | UptimeRobot API key (`ur_…` or `u0000000-…`) |
| `banned` | `bool` | Whether the user is banned |
| `ban_reason` | `str` | Reason for ban |
| `banned_at` | `datetime` | When the user was banned |
| `created_at` | `datetime` | When the user first ran `/setkey` |
| `updated_at` | `datetime` | Last API key update |
| `last_active` | `datetime` | Last API call timestamp |

**Collection: `config`**

| Field | Type | Description |
|---|---|---|
| `key` | `str` | Unique index — config key (e.g. `force_sub`) |
| `value` | `str` | Config value (e.g. `@yourchannel` or `-1001234567890`) |

---

## 🐛 Troubleshooting

| Symptom | Fix |
|---|---|
| Bot doesn't respond | Check `BOT_TOKEN` is correct and bot is not blocked |
| `api_key not found` error | Regenerate key at dashboard.uptimerobot.com → My Settings → API Settings |
| MongoDB connection error | Whitelist your server IP in Atlas → Network Access |
| `API_ID` / `API_HASH` errors | These come from [my.telegram.org](https://my.telegram.org), not BotFather |
| `/setkey` says invalid key | Key must start with `ur_` or match `u1234567-xxxx…` format |
| Multi-step flow stuck | Send `/cancel` to reset state |
| Admin commands not working | Add your Telegram user ID to `ADMINS` env variable |
| Force-sub not working | Make sure the bot is an **admin** in the channel. Use `@username` or channel ID — not a phone number |
| Inline mode not working | Enable in BotFather → Bot Settings → Inline Mode |
| Render deploy times out | Make sure `PORT` env var is set — the health server must bind a port |

---

## 📝 Notes

- **Private chats only** — group chats are not supported
- Multi-step flows (`/add`, `/addcontact`, `/addmwindow`, `/addpsp`) auto-expire after **10 minutes** of inactivity
- UptimeRobot Free plan: **50 monitors**, **10 API requests/minute**
- Alert timestamps are displayed in **IST (UTC+5:30)**
- Weekly maintenance windows: day-of-week (1 = Mon … 7 = Sun)
- Monthly maintenance windows: day-of-month (1 – 28)
- API keys are stored as plaintext — enable Atlas **Encryption at Rest** for extra security in production

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

Please keep PRs focused — one feature or fix per PR.

---

## 📄 License

MIT License — free to use, modify, and distribute. See [`LICENSE`](LICENSE) for details.
