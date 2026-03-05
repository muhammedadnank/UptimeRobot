# 📁 UptimeRobot Bot — Folder Structure

```
UptimeRobot-main/
│
├── 📁 app/
│   ├── 📄 main.py            # Module entrypoint (`python -m app.main`)
│   ├── 📁 core/
│   │   ├── 📄 db.py          # MongoDB layer (users/config/indexes)
│   │   ├── 📄 api_cache.py   # API instance cache utilities
│   │   └── 📄 uptime_robot.py# UptimeRobot API client
│   └── 📁 handlers/
│       ├── 📄 middleware.py  # check_banned · check_force_sub · check_all
│       ├── 📄 monitors.py    # /status /stats /alerts /add /pause /resume /delete /cancel
│       ├── 📄 account.py     # /account
│       ├── 📄 contacts.py    # /contacts /addcontact /delcontact
│       ├── 📄 mwindow.py     # /mwindow /addmwindow /delmwindow
│       ├── 📄 psp.py         # /psp /addpsp /delpsp
│       ├── 📄 callbacks.py   # Inline keyboard callbacks + main_keyboard()
│       ├── 📄 admin.py       # /botstats /broadcast /ban /unban /bannedlist /setfsub /delfsub /restart
│       └── 📄 inline.py      # Inline mode — @bot <query> monitor search
│
├── 📄 .env.example           # Environment variable template
├── 📄 requirements.txt       # Python dependencies
├── 📄 Procfile               # worker: python -m app.main
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
    app/handlers/*.py
          │
          ▼
  app.handlers.middleware.check_all()
    ├── app.core.db.is_banned()      ← MongoDB users collection
    └── app.core.db.get_force_sub()  ← MongoDB config collection
          │
     Passed? ──No──► Block + reply
          │
         Yes
          │
          ▼
   app.core.api_cache.get_api_for() ← returns cached UptimeRobotAPI instance
          │
          ▼
   app.core.uptime_robot.py  ← HTTPS call to api.uptimerobot.com/v2
          │
          ▼
      Reply to user
```

---

## 📦 File Responsibilities

| File | Responsibility |
|---|---|
| `app/main.py` | App entrypoint, event loop, handler registration |
| `app/core/db.py` | All MongoDB read/write |
| `app/core/api_cache.py` | API instance factory — caches per user, closes old sessions |
| `app/core/uptime_robot.py` | Pure API wrapper — no Telegram, no DB dependencies |
| `app/handlers/middleware.py` | Runs before every command — ban check + force-sub check |
| `app/handlers/monitors.py` | Monitor commands + multi-step state machine (TTL: 10 min) |
| `app/handlers/callbacks.py` | All `callback_data` routing + `main_keyboard()` builder |
| `app/handlers/admin.py` | Admin-only commands, guarded by `ADMINS` env var |
| `app/handlers/inline.py` | Inline query handler — search monitors from any chat |

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
