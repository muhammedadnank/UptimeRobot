from uptime_robot import UptimeRobotAPI
from db import get_user, update_last_active

# Cache per-user API instances so the underlying aiohttp session is reused
# across calls in the same bot process. Entries are replaced when the API
# key changes (i.e. user calls /setkey again).
_api_cache: dict[int, tuple[str, UptimeRobotAPI]] = {}


async def get_api_for(user_id: int) -> UptimeRobotAPI | None:
    """Get a per-user UptimeRobotAPI instance (cached by api_key)."""
    user = await get_user(user_id)
    if not user or not user.get("api_key"):
        return None
    api_key = user["api_key"]

    cached_key, cached_api = _api_cache.get(user_id, (None, None))
    if cached_key != api_key:
        # Key changed or first use — close old session and create new instance
        if cached_api is not None:
            await cached_api.close()
        cached_api = UptimeRobotAPI(api_key)
        _api_cache[user_id] = (api_key, cached_api)

    await update_last_active(user_id)
    return cached_api
