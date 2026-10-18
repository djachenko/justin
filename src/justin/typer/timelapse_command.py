from dataclasses import replace
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
    """``justin timelapse``: builds a Premiere project for each matched timelapse folder."""

    def __init__(
        self,
        context: Context,
        patterns: Iterable[Path],
        settings: TimelapseSettings,
    ) -> None:
        super().__init__(context, patterns)

        self.__settings = settings

    def handle_timelapse(self, timelapse_folder: Folder, extra: Extra) -> None:
        """Build a ``.prproj`` for one timelapse folder.

        Without ``--timeline-sound``, a folder with exactly one sound gets it on the
        timeline: there is nothing to choose between. With several, they all stay in
        the panel until named. Decided here, not in the settings or the generator:
        only the command sees both what the user asked for and what the folder holds.

        :param timelapse_folder: the matched timelapse folder.
        :param extra: per-photoset data from the base command; holds the photoset's name.
        """
        sources = TimelapseSources.from_folder(extra[self.SET_NAME], timelapse_folder.path)
        settings = self.__settings

        if not settings.timeline_sounds and len(sources.sounds) == 1:
            settings = replace(settings, timeline_sounds=[
                sources.sounds[0].name,
            ])

        output = generate_prproj(sources, settings)

        typer.echo(f"Created: {output}")

    def handle_common(self, folder: Folder, extra: Extra) -> None:
        """Nothing to do: only timelapse folders produce a project.

        :param folder: a matched folder that is not a timelapse.
        :param extra: per-photoset data from the base command.
        """
        pass


app = Typer()


@app.command()
def timelapse(
        context: Annotated[typer.Context, Argument()],
        pattern: Annotated[List[Path], Argument()] = [
            Path.cwd(),
        ],
        fps: Annotated[float, Option(help="Image sequence FPS")] = 10.0,
        timeline_sound: Annotated[list[str], Option(help="Sound (filename or stem) to lay on the timeline; repeatable. Default: a single sound goes on the timeline, several stay panel-only")] = [],
) -> None:
    """Generate a Premiere Pro project for each timelapse in the matched photosets."""
    settings = TimelapseSettings(
        fps=fps,
        timeline_sounds=timeline_sound
    )

    TimelapseCommand(
        context.obj,
        pattern,
        settings
    ).run()
