from datetime import timedelta
from pathlib import Path
from typing import Annotated, Iterable
from typing import List

import typer
from justin_utils.util import group_by
from typer import Argument, Typer

from justin.actions.pattern_action import Extra
from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin.shared.models.sources import parse_sources
from justin.typer.base_commands.pattern_command import PatternCommand


class DateSplitCommand(PatternCommand):
    __SIX_HOURS = timedelta(hours=6)

    def __init__(self, context: Context, patterns: Iterable[Path], epsilon: timedelta) -> None:
        super().__init__(context, patterns)

        self.__epsilon = epsilon

    def run_for_folder(self, folder: Folder, extra: Extra) -> None:
        sources = parse_sources(folder.files)

        if not sources:
            typer.echo("No sources found", err=True)

            return

        for source in sources:
            if source.exif is None:
                print(source.name)

        sources.sort(key=lambda x: x.exif.date_taken)

        pairs = zip(sources[:-1], sources[1:])

        deltas = [(a, b, b.exif.date_taken - a.exif.date_taken) for a, b in pairs]

        clusters = [[sources[0]]]

        for first, second, delta in deltas:
            if delta > self.__epsilon:
                clusters.append([])

            clusters[-1].append(second)

        # группирую кластеры, снятые в один день.
        # При этом есть сдвиг на шесть часов, т.е. снятое до 6:00 считается принадлежащим вчера
        grouped_clusters = group_by(lambda c: (c[0].exif.date_taken - DateSplitCommand.__SIX_HOURS).date(), clusters)

        for date, cluster_group in grouped_clusters.items():
            folder_name = date.strftime("%y.%m.%d")

            if len(cluster_group) == 1:
                for source in cluster_group[0]:
                    source.move_down(folder_name)
            else:
                for index, cluster in enumerate(cluster_group):
                    for source in cluster:
                        source.move_down(f"{folder_name}.cluster_{index}")


app = Typer()


@app.command()
def group(
        context: Annotated[typer.Context, Argument()],
        pattern: Annotated[List[Path], Argument()] = (Path.cwd(),),
        hours_epsilon: Annotated[int, Argument()] = 3
) -> None:
    DateSplitCommand(context.obj, pattern, timedelta(hours=hours_epsilon)).run()
