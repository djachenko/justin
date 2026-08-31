"""Загружает .env из корня репозитория до сбора тестов."""
import os
from pathlib import Path

ENV_FILE = Path(__file__).parent.parent / ".env"


def _load_env() -> None:
    if not ENV_FILE.exists():
        return

    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", maxsplit=1)
        os.environ.setdefault(name.strip(), value.strip())


_load_env()
