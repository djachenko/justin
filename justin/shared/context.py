from dataclasses import dataclass

from justin.shared.helpers.gif_maker import GifMaker
from justin.shared.models.person import PeopleRegister
from justin.shared.models.world import World
from pyvko.aspects.groups import Group
from pyvko.aspects.posts import Posts
from pyvko.pyvko_main import Pyvko


@dataclass(frozen=True)
class Context:
    world: World
    justin_group: Group
    closed_group: Group
    meeting_group: Group
    kot_i_kit_group: Group
    my_people_group: Posts

    pyvko: Pyvko

    gif_maker = GifMaker()

    my_people: PeopleRegister
    closed: PeopleRegister

    @property
    def default_group(self) -> Group:
        return self.justin_group
