# UptimeRobot Bot — Folder Structure

```
UptimeRobot-main/
│
├── bot.py                  # Entry point — Client setup, core handlers (/start, /setkey, /menu)
├── db.py                   # MongoDB — users, ban/unban, force-sub config
├── utils.py                # Per-user API instance cache (get_api_for)
├── uptime_robot.py         # UptimeRobot API wrapper (aiohttp)
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
└── railway.toml            # Railway deploy config
```

## Data Flow

```
User Message
     │
     ▼
bot.py (core handlers)
  or handlers/*.py (registered handlers)
     │
     ▼
handlers/middleware.py
  check_all() ──► db.py (is_banned)
               ──► db.py (get_force_sub)
     │
     ▼
utils.py → get_api_for()
     │
     ▼
uptime_robot.py → UptimeRobot API
     │
     ▼
Reply to user
```

## Environment Variables

| Variable     | Required | Description                        |
|--------------|----------|------------------------------------|
| API_ID       | ✅       | Telegram API ID                    |
| API_HASH     | ✅       | Telegram API Hash                  |
| BOT_TOKEN    | ✅       | Bot token from BotFather           |
| MONGODB_URI  |✅       | MongoDB connection string          |
| ADMINS       | ✅       | Space/comma separated Telegram IDs |
| PORT         | ✅       | HTTP port for health check         |
