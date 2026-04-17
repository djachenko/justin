from pathlib import Path
from typing import Annotated

import typer
from typer import Typer, Argument, Option

from justin.actions.timelapse_prproj import generate_prproj

app = Typer()


@app.command()
def timelapse(
        photoset_path: Annotated[Path, Argument(help="Path to photoset or timelapse/ folder")],
        fps: Annotated[float, Option(help="Image sequence FPS")] = 9.0,
) -> None:
    timelapse_dir = photoset_path / "timelapse" if (photoset_path / "timelapse").exists() else photoset_path
    output = generate_prproj(timelapse_dir, fps)
    typer.echo(f"Created: {output}")
