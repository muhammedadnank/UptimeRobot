import importlib
from pathlib import Path


def test_db_module_importable_and_has_get_db():
    mod = importlib.import_module("app.core.db")
    assert hasattr(mod, "get_db")


def test_db_module_uses_spaces_indentation_only():
    # Prevent tab/indentation regressions that can break deploy imports.
    content = Path("app/core/db.py").read_text(encoding="utf-8")
    assert "\t" not in content
