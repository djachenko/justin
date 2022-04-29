from dataclasses import dataclass
from functools import lru_cache

from pyvko.models.active_models import Group
from pyvko.pyvko_main import Pyvko

from justin.shared.helpers.gif_maker import GifMaker
from justin.shared.models.world import World


@dataclass(frozen=True)
class Context:
    world: World
    justin_group: Group
    closed_group: Group
    meeting_group: Group
    kot_i_kit_group: Group
    pyvko: Pyvko

    @property
    def default_group(self) -> Group:
        return self.justin_group

    @property
    @lru_cache()
    def gif_maker(self) -> GifMaker:
        return GifMaker()
