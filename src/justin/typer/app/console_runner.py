from pathlib import Path

from justin.typer.app.app import build_app
from justin.typer.app.tracker import track


def run():
    app = build_app(Path.home())

    with track():
        app()
