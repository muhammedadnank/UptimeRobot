import os
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

MONGODB_URI = os.environ.get("MONGODB_URI", "")

_client: AsyncIOMotorClient | None = None


def get_db():
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI)
    return _client["uptimebot"]


# ── Users ─────────────────────────────────────────────────────────────────────

async def get_user(telegram_id: int) -> dict | None:
    """Fetch user by telegram_id. Returns None if not found."""
    try:
        return await get_db().users.find_one({"telegram_id": telegram_id}, {"_id": 0})
    except Exception as e:
        logger.error("get_user error: %s", e)
        return None


async def upsert_user(telegram_id: int, api_key: str) -> bool:
    """Insert or update user with their UptimeRobot API key."""
    try:
        await get_db().users.update_one(
            {"telegram_id": telegram_id},
            {
                "$set": {
                    "telegram_id": telegram_id,
                    "api_key": api_key,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$setOnInsert": {
                    "created_at": datetime.now(timezone.utc),
                },
            },
            upsert=True,
        )
        return True
    except Exception as e:
        logger.error("upsert_user error: %s", e)
        return False


async def update_last_active(telegram_id: int) -> None:
    """Update last_active timestamp for a user."""
    try:
        await get_db().users.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"last_active": datetime.now(timezone.utc)}},
        )
    except Exception as e:
        logger.error("update_last_active error: %s", e)


async def delete_user(telegram_id: int) -> bool:
    """Delete a user and their stored API key."""
    try:
        result = await get_db().users.delete_one({"telegram_id": telegram_id})
        return result.deleted_count == 1
    except Exception as e:
        logger.error("delete_user error: %s", e)
        return False


# ── DB Init (indexes) ─────────────────────────────────────────────────────────

async def init_db() -> None:
    """Create indexes on startup. Call once from bot.py main()."""
    try:
        db = get_db()
        await db.users.create_index("telegram_id", unique=True)
        logger.info("✅ MongoDB connected and indexes ready.")
    except Exception as e:
        logger.error("init_db error: %s", e)
        raise
