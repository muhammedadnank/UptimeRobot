from app.handlers.middleware import _normalize_force_sub_channel


def test_normalize_accepts_username_with_at():
    assert _normalize_force_sub_channel("@my_channel") == "@my_channel"


def test_normalize_accepts_username_without_at():
    assert _normalize_force_sub_channel("my_channel") == "@my_channel"


def test_normalize_accepts_tme_link():
    assert _normalize_force_sub_channel("https://t.me/my_channel/") == "@my_channel"


def test_normalize_accepts_negative_channel_id():
    assert _normalize_force_sub_channel("-1001234567890") == -1001234567890


def test_normalize_rejects_phone_like_values():
    assert _normalize_force_sub_channel("+15551234567") is None
    assert _normalize_force_sub_channel("15551234567") is None


def test_normalize_rejects_blank_or_invalid_values():
    assert _normalize_force_sub_channel("") is None
    assert _normalize_force_sub_channel("   ") is None
    assert _normalize_force_sub_channel("not a valid chat") is None


def test_normalize_keeps_negative_int_channel_id():
    assert _normalize_force_sub_channel(-1002830331098) == -1002830331098


def test_legacy_handlers_import_still_works():
    from handlers.middleware import _normalize_force_sub_channel as legacy
    assert legacy("my_channel") == "@my_channel"

def test_legacy_root_shims_importable():
    import db as legacy_db
    import utils as legacy_utils
    import uptime_robot as legacy_uptime

    assert hasattr(legacy_db, "get_db")
    assert hasattr(legacy_utils, "get_api_for")
    assert hasattr(legacy_uptime, "UptimeRobotAPI")
