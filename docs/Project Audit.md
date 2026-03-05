# Project Audit & Naming Suggestions

_Last checked: local repository state_  

## 1) Full health check (re-run)

The following checks were run successfully:
- `pytest -q`
- `python -m compileall app`
- `python -m py_compile bot.py`

No failing tests or syntax errors were found.

---

## 2) Current structure — good parts

Your current split is mostly clean:
- `app/core/` → shared backend logic (DB/API/cache)
- `app/handlers/` → Telegram command/callback handlers
- `tests/` → unit tests
- `docs/` → project docs

This is a solid baseline. ✅

---

## 3) Better file/folder naming suggestions

Below are **optional improvements** to make naming more consistent and scalable.

### Recommended directory style

- Keep package names short + lowercase.
- Use one naming convention across handler files.
- Prefer full words instead of abbreviations for clarity.

### Suggested rename map

| Current | Suggested | Why |
|---|---|---|
| `app/handlers/mwindow.py` | `app/handlers/maintenance_windows.py` | `mwindow` is short/unclear for new contributors |
| `app/handlers/psp.py` | `app/handlers/public_status_pages.py` | Expands acronym, easier discoverability |
| `app/handlers/callbacks.py` | `app/handlers/callback_router.py` | Name reflects routing responsibility |
| `app/core/uptime_robot.py` | `app/core/uptimerobot_api.py` | Keeps API wrapper intent explicit |

> You do **not** need to rename everything now. Do this in one dedicated refactor PR to avoid import breakage.

---

## 4) Unnecessary / duplicate files check

### A) Duplicate “folder structure” docs
- `README.md` includes structure section.
- `docs/Folder Structure.md` also contains similar content.

Recommendation:
1. Keep detailed architecture only in `docs/Folder Structure.md`.
2. Keep README version short + add link to docs.

### B) `bot.py` + `app/main.py`
- If both are entrypoints, this is okay for compatibility.
- If `bot.py` only forwards to `app.main`, mention it clearly in README as legacy launcher.

---

## 5) Suggested target structure (future)

```text
UptimeRobot/
├── app/
│   ├── core/
│   │   ├── db.py
│   │   ├── api_cache.py
│   │   └── uptimerobot_api.py
│   ├── handlers/
│   │   ├── admin.py
│   │   ├── account.py
│   │   ├── monitors.py
│   │   ├── contacts.py
│   │   ├── maintenance_windows.py
│   │   ├── public_status_pages.py
│   │   ├── callback_router.py
│   │   └── inline.py
│   └── main.py
├── tests/
├── docs/
│   ├── Folder Structure.md
│   └── Project Audit.md
├── requirements.txt
├── Procfile
├── railway.toml
├── README.md
└── LICENSE
```

---

## 6) Safe cleanup order

1. Add import aliases (temporary) after each rename.
2. Update imports in all modules.
3. Run tests + compile checks.
4. Remove temporary aliases in next release.

This keeps deployment risk low.
