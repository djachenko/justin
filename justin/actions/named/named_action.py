from argparse import Namespace
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Optional, Iterable

from justin_utils import util
from pyvko.models.group import Group

from justin.actions.action import Action
from justin.shared.filesystem import FolderTree
from justin.shared.helpers.gif_maker import GifMaker
from justin.shared.models.photoset import Photoset
from justin.shared.models.world import World

Extra = Dict[str, Any]


class Context:
    def __init__(self, world: World, group: Group) -> None:
        super().__init__()

        self.__world = world
        self.__group = group

    @property
    def world(self) -> World:
        return self.__world

    @property
    def group(self) -> Group:
        return self.__group

    @property
    @lru_cache()
    def gif_maker(self) -> GifMaker:
        return GifMaker()


class NamedAction(Action):
    def perform(self, args: Namespace, world: World, group: Group) -> None:
        names = util.resolve_patterns(args.name)

        if not any(names):
            print("No items found for that pattern.")

            return

        context = Context(
            world=world,
            group=group
        )

        extra = self.get_extra(context)

        self.__perform_for_pattern(names, args, context, extra)

    # noinspection PyMethodMayBeStatic
    def get_extra(self, context: Context) -> Optional[Extra]:
        return None

    def __perform_for_pattern(self, pattern: Iterable[Path], args: Namespace, context: Context,
                              extra: Optional[Extra]) -> None:
        for path in pattern:
            photoset = Photoset(FolderTree(path))

            self.perform_for_photoset(photoset, args, context, extra)

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Optional[Extra]) \
            -> None:
        for part in photoset.parts:
            self.perform_for_part(part, args, context, extra)

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Optional[Extra]) -> None:
        assert False
