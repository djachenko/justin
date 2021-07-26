from functools import lru_cache

from pyvko.models.active_models import Group

from justin.shared.helpers.gif_maker import GifMaker
from justin.shared.models.world import World


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
