# 🤖 UptimeRobot Telegram Bot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Framework](https://img.shields.io/badge/Framework-Kurigram-blue?logo=telegram&logoColor=white)
![Database](https://img.shields.io/badge/Database-MongoDB%20Atlas-green?logo=mongodb&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Deploy](https://img.shields.io/badge/Deploy-Railway%20%7C%20Render-blueviolet)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

Full control of your **UptimeRobot** account directly from Telegram.  
**Multi-user** — each user links their own UptimeRobot API key via `/setkey`.  
Built with **Kurigram**, **aiohttp**, and **MongoDB Atlas** (free tier).

---

## ✨ Features

| Category | What you can do |
|----------|----------------|
| 🔑 **Auth** | Each user sets their own UptimeRobot API key — stored securely in MongoDB |
| 🖥️ **Monitors** | View status (Up/Down/Paused), uptime % (7d/30d/90d), response times, add/pause/resume/delete |
| 👤 **Account** | View email, monitor limit, check interval, Up/Down/Paused counts |
| 🔔 **Alert Contacts** | List, add (Email/Telegram/Webhook/SMS/Slack), delete |
| 🪟 **Maintenance Windows** | List, create (Once/Daily/Weekly/Monthly), delete |
| 📄 **Public Status Pages** | List, create, delete |
| 🔒 **Security** | Per-user API key isolation, confirmation prompt on all deletes |

---

## 🖼️ Usage Examples

### First Time Setup
```
You:  /start

Bot:  👋 UptimeRobot Bot
      ⚠️ No API key set yet. Use /setkey to get started.

You:  /setkey ur_your_api_key_here

Bot:  ✅ API key saved!
      Your UptimeRobot account is now linked.
      Use /menu or /status to get started.
```

---

### `/menu` — Interactive Control Panel
```
🖥️ UptimeRobot Control Panel
Choose an action:

[ 📊 Status  ] [ 📈 Stats   ] [ 🔔 Alerts  ]
[ 👤 Account ] [ 📬 Contacts] [ 🪟 MWindows]
[ 📄 PSP     ] [ ➕ Add Monitor             ]
```

---

### `/status` — Monitor Overview
```
📊 Monitor Status

✅ My Website [Up]
   🆔 123456789  •  🔧 HTTP(s)

✅ API Server [Up]
   🆔 123456790  •  🔧 HTTP(s)

🔴 Staging DB [Down]
   🆔 123456791  •  🔧 Ping

⏸️ Dev Server [Paused]
   🆔 123456792  •  🔧 HTTP(s)

✅ Up: 2  🔴 Down: 1  ⏸️ Paused: 1

[ 🔄 Refresh ] [ 📈 Stats ] [ 🔔 Alerts ]
[ 🔙 Menu ]
```

---

### `/add` — Add New Monitor (guided flow)
```
You:  /add

Bot:  ➕ Add New Monitor
      Step 1/3 — Enter a friendly name:
      [ ❌ Cancel ]

You:  My API

Bot:  Step 2/3 — Enter the URL:
      [ ❌ Cancel ]

You:  https://api.mysite.com/health

Bot:  Step 3/3 — Choose monitor type:
      [ 🌐 HTTP(s) ] [ 🔑 Keyword ]
      [ 📡 Ping    ] [ 🔌 Port    ]

You:  [ 🌐 HTTP(s) ]

Bot:  ✅ Monitor created!
      📛 Name: My API
      🔗 URL:  https://api.mysite.com/health
      🔧 Type: HTTP(s)
      🆔 ID:   987654321
```

---

### `/stats` — Uptime & Response Times
```
📈 Monitor Stats

🖥️ My Website
   ⏱ Avg: 142 ms | 7d: 99.98% | 30d: 99.95% | 90d: 99.91%

🖥️ API Server
   ⏱ Avg: 87 ms  | 7d: 100%   | 30d: 99.99% | 90d: 99.97%

[ 📊 Status ] [ 🔔 Alerts ]
[ 🔙 Menu ]
```

---

### `/alerts` — Recent Alert Logs
```
🔔 Recent Alerts

🖥️ Staging DB
   🔴 2025-01-15 03:42 — Went DOWN: Connection refused
   ✅ 2025-01-15 03:50 — Came UP

[ 📊 Status ] [ 📈 Stats ]
[ 🔙 Menu ]
```

---

## 📋 Commands

### 🔑 Account Setup
| Command | Description |
|---------|-------------|
| `/setkey <api_key>` | Link your UptimeRobot API key |
| `/mykey` | Check if your API key is set |
| `/deletekey` | Remove your stored API key |

### General
| Command | Description |
|---------|-------------|
| `/start` | Help message & full command list |
| `/menu` | Interactive inline button panel |
| `/cancel` | Cancel any in-progress operation |

### 🖥️ Monitors
| Command | Description |
|---------|-------------|
| `/status` | Status of all monitors |
| `/stats` | Uptime % & avg response times |
| `/alerts` | Recent alert logs (last 3 per monitor) |
| `/add` | Add a new monitor (guided, 3-step) |
| `/pause <id>` | Pause a monitor |
| `/resume <id>` | Resume a monitor |
| `/delete <id>` | Delete a monitor (with confirmation) |

### 👤 Account
| Command | Description |
|---------|-------------|
| `/account` | View account details |

### 🔔 Alert Contacts
| Command | Description |
|---------|-------------|
| `/contacts` | List all alert contacts |
| `/addcontact` | Add a new contact (guided) |
| `/delcontact <id>` | Delete a contact (with confirmation) |

### 🪟 Maintenance Windows
| Command | Description |
|---------|-------------|
| `/mwindow` | List all maintenance windows |
| `/addmwindow` | Create a new window (guided) |
| `/delmwindow <id>` | Delete a window (with confirmation) |

### 📄 Public Status Pages
| Command | Description |
|---------|-------------|
| `/psp` | List all status pages |
| `/addpsp` | Create a new status page (guided) |
| `/delpsp <id>` | Delete a status page (with confirmation) |

> 💡 Use `/status` to find monitor IDs for pause/resume/delete commands.

---

## 📁 Project Structure

```
uptimebot/
├── bot.py                  # Entry point — /start, /menu, /setkey, /mykey, /deletekey
├── db.py                   # MongoDB layer — user CRUD via motor (async)
├── uptime_robot.py         # Async UptimeRobot API wrapper (aiohttp)
├── utils.py                # get_api_for(user_id) — per-user API instance
├── requirements.txt        # Python dependencies
├── Procfile                # Process config (Railway / Render)
├── railway.toml            # Railway deployment config
├── .env.example            # Environment variable template
└── handlers/
    ├── __init__.py
    ├── monitors.py         # Monitor commands + multi-step state machine (TTL: 10 min)
    ├── account.py          # /account command
    ├── contacts.py         # Alert contact commands
    ├── mwindow.py          # Maintenance window commands
    ├── psp.py              # Public status page commands
    └── callbacks.py        # All inline keyboard button handlers
```

---

## 🔧 Local Setup

### Step 1 — Get Credentials

| Variable | Where to get it |
|----------|----------------|
| `API_ID` | [my.telegram.org](https://my.telegram.org) → API Development Tools |
| `API_HASH` | [my.telegram.org](https://my.telegram.org) → API Development Tools |
| `BOT_TOKEN` | Telegram → `@BotFather` → `/newbot` |
| `MONGODB_URI` | [cloud.mongodb.com](https://cloud.mongodb.com) → Free Cluster → Connect → Drivers (see below) |

> **UptimeRobot API Key** is no longer an env variable — each user sets it themselves via `/setkey` in the bot.

---

### Step 2 — MongoDB Atlas Setup (Free)

1. Go to [cloud.mongodb.com](https://cloud.mongodb.com) → **Sign up / Log in**
2. **Create a free cluster** → Choose **M0 Free** tier
3. **Database Access** → Add a user with password
4. **Network Access** → Allow access from anywhere (`0.0.0.0/0`)
5. **Connect** → **Drivers** → Copy the connection string:
   ```
   mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
6. Replace `<user>` and `<password>` with your DB credentials

---

### Step 3 — Install & Run

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/uptimebot.git
cd uptimebot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and fill in your values

# Run
python bot.py
```

---

## ☁️ Deployment

### Railway

1. Push to GitHub:
```bash
git init && git add . && git commit -m "init"
git remote add origin https://github.com/YOUR_USERNAME/uptimebot.git
git push -u origin main
```

2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
3. Select your repository
4. In the **Variables** tab, add:

```
API_ID       = 12345678
API_HASH     = your_api_hash
BOT_TOKEN    = your_bot_token
MONGODB_URI  = mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/...
```

5. Auto deploy! ✅

---

### Render

1. Push to GitHub (same as above)
2. Go to [render.com](https://render.com) → **New** → **Background Worker**
3. Connect your repository
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. Add environment variables (same as Railway)
6. Click **Create Background Worker** → Deploy! ✅

---

## ⚙️ Environment Variables

```env
# Telegram MTProto credentials — from my.telegram.org
API_ID=12345678
API_HASH=your_api_hash_here

# Bot token — from @BotFather
BOT_TOKEN=your_bot_token_here

# MongoDB Atlas connection string — from cloud.mongodb.com
# Replace <user> and <password> with your DB credentials
MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

> Each user's UptimeRobot API key is stored in MongoDB — no longer an env variable.

---

## 🛠️ Tech Stack

| Package | Purpose |
|---------|---------|
| [`kurigram`](https://github.com/KurimuzonAkuma/pyrogram) | Telegram MTProto framework — actively maintained Pyrogram fork |
| [`motor`](https://motor.readthedocs.io) | Async MongoDB driver for Python |
| [`aiohttp`](https://docs.aiohttp.org) | Async HTTP client for UptimeRobot API calls |

---

## 🗄️ Database Schema

**Collection: `users`**

| Field | Type | Description |
|-------|------|-------------|
| `telegram_id` | `int` | Unique index — Telegram user ID |
| `api_key` | `str` | UptimeRobot API key (starts with `ur_`) |
| `created_at` | `datetime` | First time user ran /setkey |
| `updated_at` | `datetime` | Last time API key was updated |
| `last_active` | `datetime` | Last time user made an API call |

---

## 📝 Notes

- Works in **private chats only** — groups are not supported
- Multi-step flows (`/add`, `/addcontact`, `/addmwindow`, `/addpsp`) can be cancelled anytime with `/cancel` or the **❌ Cancel** button
- Abandoned sessions auto-expire after **10 minutes**
- UptimeRobot Free plan: **10 API requests/minute** rate limit
- Weekly maintenance windows require a day-of-week (1 = Mon … 7 = Sun)
- Monthly maintenance windows require a day-of-month (1 – 28)
- API keys are stored as plain text in MongoDB — use Atlas **encryption at rest** for extra security

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

Please keep PRs focused — one feature or fix per PR.

---

## 📄 License

This project is licensed under the **MIT License** — free to use, modify, and distribute.  
See [`LICENSE`](LICENSE) for full details.
