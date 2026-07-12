from pathlib import Path
from typing import Annotated, Iterable, List

import typer
from typer import Typer, Argument, Option

from justin.actions.timelapse_prproj import TimelapseSettings, generate_prproj
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
        fps: float,
        timeline_sounds: list[str],
    ) -> None:
        super().__init__(context, patterns)

        self.__fps = fps
        self.__timeline_sounds = timeline_sounds

    def handle_timelapse(self, timelapse_folder: Folder, extra: Extra) -> None:
        name = extra[TimelapseCommand.SET_NAME]
        sources = TimelapseSources.from_folder(name, timelapse_folder.path)
        settings = TimelapseSettings(sources=sources, fps=self.__fps, timeline_sounds=self.__timeline_sounds)

        output = generate_prproj(settings)

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
    TimelapseCommand(context.obj, pattern, fps, timeline_sound).run()
