from argparse import Namespace
from datetime import timedelta
from pathlib import Path
from typing import List

from justin.actions.pattern_action import PatternAction, Extra
from justin.shared.filesystem import Folder
from justin.shared.models.sources import parse_sources
from justin_utils.cli import Context, Parameter
from justin_utils.util import group_by


class DateSplitAction(PatternAction):
    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter(flags=["-e", "--epsilon"], default=3, type=lambda x: timedelta(hours=int(x)))
        ]

    def perform_for_path(self, path: Path, args: Namespace, context: Context, extra: Extra) -> None:
        sources = parse_sources(Folder(path).files)

        if not sources:
            return

        for source in sources:
            if source.exif is None:
                print(source.name)

        sources.sort(key=lambda x: x.exif.date_taken)

        pairs = zip(sources[:-1], sources[1:])

        deltas = [(a, b, b.exif.date_taken - a.exif.date_taken) for a, b in pairs]

        clusters = [[sources[0]]]

        epsilon = timedelta(hours=3)

        for first, second, delta in deltas:
            if delta > epsilon:
                clusters.append([])

            clusters[-1].append(second)

        six_hours = timedelta(hours=6)

        grouped_clusters = group_by(lambda c: (c[0].exif.date_taken - six_hours).date(), clusters)

        for date, cluster_group in grouped_clusters.items():
            folder_name = date.strftime("%y.%m.%d")

            if len(cluster_group) == 1:
                for source in cluster_group[0]:
                    source.move_down(folder_name)
            else:
                for index, cluster in enumerate(cluster_group):
                    for source in cluster:
                        source.move_down(f"{folder_name}.cluster_{index}")
