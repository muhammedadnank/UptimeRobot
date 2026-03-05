# Project Audit & Structure Suggestions

This audit gives a cleaner folder strategy and flags files that look redundant.

## Current structure status

The codebase already follows a good module split:
- `app/core/` for data/API layers.
- `app/handlers/` for Telegram command/callback logic.
- `tests/` for unit tests.
- `docs/` for project documentation.

## Suggested target structure

```text
UptimeRobot/
├── app/
│   ├── core/                # DB + UptimeRobot API + shared caches
│   ├── handlers/            # command/callback/inline handlers
│   └── main.py              # app entrypoint
├── tests/                   # unit tests
├── docs/                    # architecture + setup docs
├── bot.py                   # optional compatibility launcher
├── requirements.txt
├── Procfile
├── railway.toml
├── README.md
└── LICENSE
```

## Unnecessary or duplicate files to review

1. `db.py` (project root)
   - Currently a compatibility re-export of `app.core.db`.
   - Keep it only if old scripts import `db` directly.
   - If no legacy usage exists, remove it in a future cleanup.

2. Duplicate structure text in `README.md`
   - The `Project Structure` block is duplicated.
   - Keep one canonical version and link to docs.

3. `docs/Folder Structure.md`
   - Useful, but overlaps with README section.
   - Keep docs version as source-of-truth and shorten README.

## Recommended cleanup order

1. Keep compatibility layer (`db.py`) for one release.
2. Add deprecation note in README/docs.
3. Remove compatibility file in next major/minor release.
