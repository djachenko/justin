from argparse import Namespace
from pathlib import Path
from typing import Dict, Any, Iterable

from justin.actions.action import Action
from justin.shared.context import Context
from justin.shared.filesystem import FolderTree
from justin.shared.models.photoset import Photoset
from justin_utils import util

Extra = Dict[str, Any]


class NamedAction(Action):
    def perform(self, args: Namespace, context: Context) -> None:
        names = list(util.resolve_patterns(args.name))

        if not any(names):
            print("No items found for that pattern.")

            return

        extra = self.get_extra(context)

        self.__perform_for_pattern(names, args, context, extra)

    # noinspection PyMethodMayBeStatic
    def get_extra(self, context: Context) -> Extra:
        return {}

    def __perform_for_pattern(self, pattern: Iterable[Path], args: Namespace, context: Context, extra: Extra) -> None:
        for path in pattern:
            photoset = Photoset(FolderTree(path))

            self.perform_for_photoset(photoset, args, context, extra.copy())

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        for part in photoset.parts:
            self.perform_for_part(part, args, context, extra.copy())

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        assert False
