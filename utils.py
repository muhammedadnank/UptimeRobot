from uptime_robot import UptimeRobotAPI
from db import get_user, update_last_active


async def get_api_for(user_id: int) -> UptimeRobotAPI | None:
    """Get a per-user UptimeRobotAPI instance from MongoDB."""
    user = await get_user(user_id)
    if not user or not user.get("api_key"):
        return None
    await update_last_active(user_id)
    return UptimeRobotAPI(user["api_key"])
