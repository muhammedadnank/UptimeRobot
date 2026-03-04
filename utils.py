import os
from uptime_robot import UptimeRobotAPI

ALLOWED_USERS_RAW = os.environ.get("ALLOWED_USERS", "")
_api_instance: UptimeRobotAPI | None = None


def init_api(key: str):
    global _api_instance
    _api_instance = UptimeRobotAPI(key)


def get_api() -> UptimeRobotAPI:
    if _api_instance is None:
        raise RuntimeError("API not initialized. Call init_api() first.")
    return _api_instance


def get_allowed_users() -> list[int]:
    if not ALLOWED_USERS_RAW:
        return []
    return [int(x.strip()) for x in ALLOWED_USERS_RAW.split(",") if x.strip()]


def is_authorized(user_id: int) -> bool:
    allowed = get_allowed_users()
    return (not allowed) or (user_id in allowed)
