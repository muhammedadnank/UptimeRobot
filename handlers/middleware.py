"""Backward-compatible handler re-export."""

from app.handlers.middleware import *  # noqa: F401,F403
from app.handlers.middleware import _normalize_force_sub_channel  # noqa: F401
