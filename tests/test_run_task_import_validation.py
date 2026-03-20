from __future__ import annotations

from pathlib import Path


from agents.run_task import validate_imports


def test_valid_repo_local_symbol_import_passes_with_bundled_module() -> None:
    bundle = {
        "src/tradingbot/__init__.py": "",
        "src/tradingbot/sample_mod.py": "class Example:\n    pass\n",
        "tests/test_sample.py": "from tradingbot.sample_mod import Example\n",
    }

    ok, msg = validate_imports(bundle)

    assert ok
    assert msg == ""


def test_missing_repo_local_module_fails() -> None:
    bundle = {
        "src/tradingbot/__init__.py": "",
        "tests/test_missing.py": "from tradingbot.missing_mod import Example\n",
    }

    ok, msg = validate_imports(bundle)

    assert not ok
    assert "imports missing module 'tradingbot.missing_mod'" in msg


def test_existing_module_but_missing_symbol_fails() -> None:
    bundle = {
        "src/tradingbot/__init__.py": "",
        "src/tradingbot/missing_symbol_mod.py": "class Present:\n    pass\n",
        "tests/test_missing_symbol.py": "from tradingbot.missing_symbol_mod import Absent\n",
    }

    ok, msg = validate_imports(bundle)

    assert not ok
    assert "imports missing symbol 'Absent' from 'tradingbot.missing_symbol_mod'" in msg


def test_alias_import_of_existing_symbol_passes() -> None:
    bundle = {
        "src/builder/__init__.py": "",
        "src/builder/orchestrator/__init__.py": "",
        "src/builder/orchestrator/aliased.py": "class AliasTarget:\n    pass\n",
        "tests/test_alias.py": "from builder.orchestrator.aliased import AliasTarget as Renamed\n",
    }

    ok, msg = validate_imports(bundle)

    assert ok
    assert msg == ""


def test_star_import_is_ignored_and_passes() -> None:
    bundle = {
        "src/tradingbot/__init__.py": "",
        "src/tradingbot/star_mod.py": "class Visible:\n    pass\n",
        "tests/test_star.py": "from tradingbot.star_mod import *\n",
    }

    ok, msg = validate_imports(bundle)

    assert ok
    assert msg == ""


def test_bundled_module_symbol_definitions_are_recognized_without_disk_write() -> None:
    module_path = Path("src") / "builder" / "orchestrator" / "bundled_mod.py"
    bundle = {
        "src/builder/__init__.py": "",
        "src/builder/orchestrator/__init__.py": "",
        module_path.as_posix(): "def bundled_function():\n    return 1\n",
        "tests/test_bundled.py": "from builder.orchestrator.bundled_mod import bundled_function\n",
    }

    ok, msg = validate_imports(bundle)

    assert ok
    assert msg == ""


def test_package_init_exports_are_recognized_when_present_in_bundle() -> None:
    bundle = {
        "src/tradingbot/__init__.py": "",
        "src/tradingbot/export_pkg/__init__.py": "from .impl import Exported\n",
        "src/tradingbot/export_pkg/impl.py": "class Exported:\n    pass\n",
        "tests/test_export_pkg.py": "from tradingbot.export_pkg import Exported\n",
    }

    ok, msg = validate_imports(bundle)

    assert ok
    assert msg == ""
