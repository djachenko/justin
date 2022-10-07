from abc import ABC
from argparse import Namespace
from pathlib import Path
from typing import List

from justin_utils import util
from justin_utils.cli import Parameter, Action, Context

from justin.shared.filesystem import FolderTree
from justin.shared.models.photoset import Photoset

Extra = Dict[str, Any]


class PatternAction(Action, ABC):
    @property
    def parameters(self) -> List[Parameter]:
        return [
            Parameter("pattern", nargs="*", default=[Path.cwd().as_posix()])
        ]

    def perform(self, args: Namespace, context: Context) -> None:
        pattern: List[str] = args.pattern

        paths = list(util.resolve_patterns(*pattern))

        if not any(paths):
            print("No items found for that pattern.")

            return

        extra = self.get_extra(context)

        self.perform_for_pattern(paths, args, context, extra.copy())

    def get_extra(self, context: Context) -> Extra:
        return {}

    def perform_for_pattern(self, paths: List[Path], args: Namespace, context: Context, extra: Extra) -> None:
        for path in paths:
            self.perform_for_path(path, args, context, extra.copy())

    def perform_for_path(self, path: Path, args: Namespace, context: Context, extra: Extra) -> None:
        photoset = Photoset(FolderTree(path))

        self.perform_for_photoset(photoset, args, context, extra.copy())

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        for part in photoset.parts:
            self.perform_for_part(part, args, context, extra.copy())

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        assert False
