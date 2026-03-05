"""MongoDB data layer for user and bot configuration state."""

import logging
import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)
MONGODB_URI = os.environ.get("MONGODB_URI", "")

_client: AsyncIOMotorClient | None = None


def get_db():
     """Return the shared MongoDB database handle."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI)
    return _client["uptimebot"]


# Users

async def get_user(telegram_id: int) -> dict | None:
    try:
        return await get_db().users.find_one({"telegram_id": telegram_id}, {"_id": 0})
    except Exception as e:
        logger.error("get_user error: %s", e)
        return None


async def upsert_user(telegram_id: int, api_key: str) -> bool:
    try:
        now = datetime.now(timezone.utc)
        await get_db().users.update_one(
            {"telegram_id": telegram_id},
            {
                "$set": {
                    "telegram_id": telegram_id,
                    "api_key": api_key,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                    "banned": False,
                    "ban_reason": "",
                },
            },
            upsert=True,
        )
        return True
    except Exception as e:
        logger.error("upsert_user error: %s", e)
        return False


async def update_last_active(telegram_id: int) -> None:
    try:
        await get_db().users.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"last_active": datetime.now(timezone.utc)}},
        )
    except Exception as e:
        logger.error("update_last_active error: %s", e)


async def delete_user(telegram_id: int) -> bool:
    try:
        result = await get_db().users.delete_one({"telegram_id": telegram_id})
        return result.deleted_count == 1
    except Exception as e:
        logger.error("delete_user error: %s", e)
        return False


async def get_all_users():
    """Async generator yielding all user documents."""
    try:
        async for user in get_db().users.find({}, {"_id": 0}):
            yield user
    except Exception as e:
        logger.error("get_all_users error: %s", e)


async def total_users_count() -> int:
    try:
        return await get_db().users.count_documents({})
    except Exception as e:
        logger.error("total_users_count error: %s", e)
        return 0

# Ban / Unban
async def ban_user(telegram_id: int, reason: str = "No reason provided") -> bool:
    """Ban a user. Creates a minimal record if they do not exist yet."""
     try:
        await get_db().users.update_one(
            {"telegram_id": telegram_id},
            {
                "$set": {
                    "telegram_id": telegram_id,
                    "banned": True,
                    "ban_reason": reason,
                    "banned_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        return True
    except Exception as e:
        logger.error("ban_user error: %s", e)
        return False


async def unban_user(telegram_id: int) -> bool:
    """Unban a user. Returns True if user exists (even if already unbanned)."""
    try:
        result = await get_db().users.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"banned": False, "ban_reason": ""}},
        )
        return result.matched_count == 1
    except Exception as e:
        logger.error("unban_user error: %s", e)
        return False


async def is_banned(telegram_id: int) -> tuple[bool, str]:
    """Return (is_banned, reason)."""
    try:
        user = await get_db().users.find_one({"telegram_id": telegram_id}, {"_id": 0})
        if user and user.get("banned"):
            return True, user.get("ban_reason", "No reason provided")
        return False, ""
    except Exception as e:
        logger.error("is_banned error: %s", e)
        return False, ""


async def get_banned_users():
    """Async generator yielding all banned user documents."""
    try:
        async for user in get_db().users.find({"banned": True}, {"_id": 0}):
            yield user
    except Exception as e:
        logger.error("get_banned_users error: %s", e)


async def total_banned_count() -> int:
    try:
        return await get_db().users.count_documents({"banned": True})
    except Exception as e:
        logger.error("total_banned_count error: %s", e)
        return 0


# Force subscribe
async def get_force_sub() -> str | None:
    """Get the current force-sub channel username/id from DB config."""
    try:
        doc = await get_db().config.find_one({"key": "force_sub"})
        return doc.get("value") if doc else None
    except Exception as e:
        logger.error("get_force_sub error: %s", e)
        return None


async def set_force_sub(channel: str | None) -> bool:
    """Set or clear the force-sub channel. Pass None to disable."""
    try:
        if channel is None:
            await get_db().config.delete_one({"key": "force_sub"})
        else:
            await get_db().config.update_one(
                {"key": "force_sub"},
                {"$set": {"key": "force_sub", "value": channel}},
                upsert=True,
            )
        return True
    except Exception as e:
        logger.error("set_force_sub error: %s", e)
        return False


# DB init (indexes)
async def init_db() -> None:
    """Create indexes on startup. Call once from app startup."""
    try:
        db = get_db()
        await db.users.create_index("telegram_id", unique=True)
        await db.config.create_index("key", unique=True)
        logger.info("MongoDB connected and indexes ready.")
    except Exception as e:
        logger.error("init_db error: %s", e)
        raise
