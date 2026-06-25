try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]
from pathlib import Path

import pytest


@pytest.mark.xfail(strict=False, reason="mypy debt: modules with suppressed errors in pyproject.toml")
def test_no_mypy_suppressed_modules() -> None:
    with open(Path(__file__).parent.parent / "pyproject.toml", "rb") as f:
        config = tomllib.load(f)

    overrides = config.get("tool", {}).get("mypy", {}).get("overrides", [])
    suppressed = [m for o in overrides if o.get("ignore_errors") for m in o.get("module", [])]

    assert not suppressed, f"{len(suppressed)} modules still suppressed — remove from pyproject.toml overrides:\n" + "\n".join(suppressed)
