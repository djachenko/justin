import sys
from pathlib import Path
import time


def run():
    from coverage import Coverage

    data_dir = Path.home() / ".justin" / "coverage"
    data_dir.mkdir(parents=True, exist_ok=True)
    data_file = data_dir / f"{int(time.time() * 1000)}.coverage"

    cov = Coverage(data_file=str(data_file))
    cov.config.disable_warnings = ["module-not-measured"]
    cov.start()

    try:
        from justin.typer.app.app import build_app
        app = build_app(Path.home())
        app()
    finally:
        cov.stop()
        cov.save()
