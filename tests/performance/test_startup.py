"""Application start-up speed.

justin is run dozens of times a day, and a slower start goes unnoticed: it arrives with one
new import at the top of some module and shows itself nowhere else. These are ceilings,
not benchmarks — set about three times above the measured values, to catch a collapse
rather than machine noise.

Measured 2026-08-31, macOS, warm cache: --help 0.48–0.62 s, app import 0.34–0.53 s.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

JUSTIN = str(Path(sys.executable).parent / "justin")  # the justin next to this interpreter

HELP_BUDGET = 2.0
IMPORT_BUDGET = 1.5
COMPLETION_BUDGET = 1.0  # pressed with Tab, so the ceiling is lower than the rest
RUNS = 3


def _fastest(command: list[str], env: dict[str, str] | None = None) -> float:
    timings = []

    for _ in range(RUNS):
        started = time.monotonic()
        result = subprocess.run(command, capture_output=True, text=True, env=env)
        timings.append(time.monotonic() - started)

        assert result.returncode == 0, f"{command} failed: {result.stderr[-500:]}"

    return min(timings)


def _completion(word: str) -> dict[str, str]:
    return {
        **os.environ,
        "_JUSTIN_COMPLETE": "complete_zsh",
        "COMP_WORDS": f"justin {word}",
        "COMP_CWORD": "1",
    }


@pytest.mark.performance
class TestStartup:
    def test_help_is_fast(self) -> None:
        elapsed = _fastest([JUSTIN, "--help"])

        assert elapsed < HELP_BUDGET, \
            f"justin --help starts in {elapsed:.2f} s against a {HELP_BUDGET} ceiling"

    def test_app_import_is_fast(self) -> None:
        """Apart from help: tells slow imports from slow command assembly."""
        elapsed = _fastest([sys.executable, "-c", "import justin.typer.app.app"])

        assert elapsed < IMPORT_BUDGET, \
            f"importing the app takes {elapsed:.2f} s against a {IMPORT_BUDGET} ceiling"

    def test_completion_is_fast(self) -> None:
        elapsed = _fastest([JUSTIN], env=_completion(""))

        assert elapsed < COMPLETION_BUDGET, \
            f"completion answers in {elapsed:.2f} s against a {COMPLETION_BUDGET} ceiling"


@pytest.mark.performance
class TestCompletion:
    def test_commands_are_listed(self) -> None:
        result = subprocess.run([JUSTIN], capture_output=True, text=True, env=_completion("se"))

        assert result.returncode == 0, result.stderr[-500:]
        assert "setup-event" in result.stdout, result.stdout[:300]
