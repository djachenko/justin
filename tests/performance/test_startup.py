"""Скорость старта приложения.

`justin` — ежедневный инструмент, его запускают десятки раз в день, и деградация старта
замечается не сразу: она приходит вместе с одним новым импортом наверху какого-нибудь
модуля и больше никак себя не проявляет. Здесь — потолок, а не бенчмарк: числа взяты
с запасом примерно втрое от измеренного, чтобы тест ловил обвал, а не шум машины.

Замеры 31.08.2026, macOS, прогретый кеш: `--help` — 0.48–0.62 с, импорт app — 0.34–0.53 с.
Потолки ниже — страховка от обвала, а не цель: целевое время старта ещё не выбрано.
"""
import subprocess
import sys
import time

import pytest

HELP_BUDGET = 2.0
IMPORT_BUDGET = 1.5
RUNS = 3


def _fastest(command: list[str]) -> float:
    """Лучшее из нескольких: медленные прогоны — это шум соседних процессов, а не код."""
    timings = []

    for _ in range(RUNS):
        started = time.monotonic()
        result = subprocess.run(command, capture_output=True, text=True)
        timings.append(time.monotonic() - started)

        assert result.returncode == 0, f"{command} упал: {result.stderr[-500:]}"

    return min(timings)


@pytest.mark.performance
def test_help_is_fast() -> None:
    """Полный путь: запуск интерпретатора, сборка Typer-приложения, вывод справки."""
    elapsed = _fastest(["justin", "--help"])

    assert elapsed < HELP_BUDGET, f"justin --help стартует {elapsed:.2f} с при потолке {HELP_BUDGET}"


@pytest.mark.performance
def test_app_import_is_fast() -> None:
    """Отдельно импорт: если просела справка, здесь видно, импорты это или сборка команд."""
    elapsed = _fastest([sys.executable, "-c", "import justin.typer.app.app"])

    assert elapsed < IMPORT_BUDGET, f"импорт приложения {elapsed:.2f} с при потолке {IMPORT_BUDGET}"
