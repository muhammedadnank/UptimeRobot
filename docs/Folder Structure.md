# 📁 UptimeRobot Bot — Folder Structure

```
UptimeRobot-main/
│
── 📁 app/
│   ├── 📄 main.py            # Module entrypoint (`python -m app.main`)
│   ├── 📁 core/
│   │   ├── 📄 db.py          # Compatibility wrapper for DB module
│   │   ├── 📄 api_cache.py   # Compatibility wrapper for API cache utils
│   │   └── 📄 uptime_robot.py# Compatibility wrapper for API client
│   └── 📁 handlers/          # Compatibility namespace for handlers package
│
├── 📄 bot.py                 # Legacy entrypoint (backward compatible)
├── 📄 db.py                  # MongoDB — users CRUD, ban/unban, force-sub config, indexes
├── 📄 utils.py               # get_api_for() — per-user API instance cache
├── 📄 uptime_robot.py        # UptimeRobot REST API wrapper (aiohttp, session reuse)
│
├── 📁 handlers/
│   ├── 📄 __init__.py
│   ├── 📄 middleware.py      # check_banned · check_force_sub · check_all
│   ├── 📄 monitors.py        # /status /stats /alerts /add /pause /resume /delete /cancel
│   ├── 📄 account.py         # /account
│   ├── 📄 contacts.py        # /contacts /addcontact /delcontact
│   ├── 📄 mwindow.py         # /mwindow /addmwindow /delmwindow
│   ├── 📄 psp.py             # /psp /addpsp /delpsp
│   ├── 📄 callbacks.py       # Inline keyboard callbacks + main_keyboard()
│   ├── 📄 admin.py           # /botstats /broadcast /ban /unban /bannedlist /setfsub /delfsub /restart
│   └── 📄 inline.py          # Inline mode — @bot <query> monitor search
│
├── 📄 .env.example           # Environment variable template
├── 📄 requirements.txt       # Python dependencies
├── 📄 Procfile               # worker: python bot.py
├── 📄 railway.toml           # Railway deploy config
├── 📄 README.md              # Documentation
└── 📄 LICENSE                # MIT License
```

---

## 🔄 Request Flow

```
User sends message / callback
          │
          ▼
    handlers/*.py
          │
          ▼
  middleware.check_all()
    ├── db.is_banned()         ← MongoDB users collection
    └── db.get_force_sub()     ← MongoDB config collection
          │
     Passed? ──No──► Block + reply
          │
         Yes
          │
          ▼
   utils.get_api_for()         ← returns cached UptimeRobotAPI instance
          │
          ▼
   uptime_robot.py             ← HTTPS call to api.uptimerobot.com/v2
          │
          ▼
      Reply to user
```

---

## 📦 File Responsibilities

| File | Responsibility |
|---|---|
| `bot.py` | App entry point, event loop, handler registration |
| `db.py` | All MongoDB read/write — never imported by `uptime_robot.py` |
| `utils.py` | API instance factory — caches per user, closes old sessions |
| `uptime_robot.py` | Pure API wrapper — no Telegram, no DB dependencies |
| `handlers/middleware.py` | Runs before every command — ban check + force-sub check |
| `handlers/monitors.py` | Monitor commands + multi-step state machine (TTL: 10 min) |
| `handlers/callbacks.py` | All `callback_data` routing + `main_keyboard()` builder |
| `handlers/admin.py` | Admin-only commands, guarded by `ADMINS` env var |
| `handlers/inline.py` | Inline query handler — search monitors from any chat |

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `API_ID` | ✅ | Telegram API ID — my.telegram.org |
| `API_HASH` | ✅ | Telegram API Hash — my.telegram.org |
| `BOT_TOKEN` | ✅ | Bot token — @BotFather |
| `MONGODB_URI` | ✅ | MongoDB connection string |
| `ADMINS` | ✅ | Space/comma separated Telegram user IDs |
| `PORT` | ✅ | HTTP port for health check (Render default: 10000) |
