import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.version_info < (3, 11), reason="tomllib requires Python 3.11+")
@pytest.mark.xfail(strict=False, reason="mypy debt: modules with suppressed errors in pyproject.toml")
def test_no_mypy_suppressed_modules() -> None:
    import tomllib

    with open(Path(__file__).parent.parent / "pyproject.toml", "rb") as f:
        config = tomllib.load(f)

    overrides = config.get("tool", {}).get("mypy", {}).get("overrides", [])
    suppressed = [m for o in overrides if o.get("ignore_errors") for m in o.get("module", [])]

    assert not suppressed, f"{len(suppressed)} modules still suppressed — remove from pyproject.toml overrides:\n" + "\n".join(suppressed)
