from pathlib import Path
from typing import Annotated, Iterable, List

import typer
from typer import Typer, Argument, Option

from justin.actions.timelapse_prproj import generate_prproj
from justin.actions.timelapse_settings import TimelapseSettings
from justin.actions.timelapse_sources import TimelapseSources
from justin.shared.context import Context
from justin.typer.base_commands.pattern_command import Extra
from justin.typer.base_commands.destinations_aware_command import DestinationsAwareCommand
from justin_utils.filesystem import Folder


class TimelapseCommand(DestinationsAwareCommand):
    def __init__(
        self,
        context: Context,
        patterns: Iterable[Path],
        settings: TimelapseSettings,
    ) -> None:
        super().__init__(context, patterns)

        self.__settings = settings

    def handle_timelapse(self, timelapse_folder: Folder, extra: Extra) -> None:
        sources = TimelapseSources.from_folder(extra[self.SET_NAME], timelapse_folder.path)
        output = generate_prproj(sources, self.__settings)

        typer.echo(f"Created: {output}")

    def handle_common(self, folder: Folder, extra: Extra) -> None:
        pass


app = Typer()


@app.command()
def timelapse(
        context: Annotated[typer.Context, Argument()],
        pattern: Annotated[List[Path], Argument()] = (Path.cwd(),),
        fps: Annotated[float, Option(help="Image sequence FPS")] = 10.0,
        timeline_sound: Annotated[list[str], Option(help="Sound (filename or stem) to lay on the timeline; repeatable. Default: all sounds panel-only")] = [],
) -> None:
    settings = TimelapseSettings(fps=fps, timeline_sounds=timeline_sound)

    TimelapseCommand(
        context.obj,
        pattern,
        settings
    ).run()
