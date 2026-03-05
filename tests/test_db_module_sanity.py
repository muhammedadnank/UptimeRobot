import importlib
import py_compile
from pathlib import Path


def test_db_module_importable_and_has_get_db():
    mod = importlib.import_module("app.core.db")
    assert hasattr(mod, "get_db")


def test_db_module_compiles_cleanly():
    # Catch syntax/indentation problems exactly how deploy import does.
    py_compile.compile("app/core/db.py", doraise=True)


def test_db_module_uses_safe_indentation_characters_only():
    # Prevent tabs / odd unicode whitespace in indentation.
    lines = Path("app/core/db.py").read_text(encoding="utf-8").splitlines()
    for line in lines:
        prefix = ""
        for ch in line:
            if ch in (" ", "\t"):
                prefix += ch
            else:
                break
        assert "\t" not in prefix
        assert all(ord(ch) == 32 for ch in prefix)
