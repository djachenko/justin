from argparse import Namespace

from pyvko.models.group import Group

from v3_0.actions.named.named_action import NamedAction
from v3_0.shared.helpers.gif_maker import GifMaker
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class MakeGifAction(NamedAction):
    def perform_for_photoset(self, photoset: Photoset, args: Namespace, world: World, group: Group) -> None:
        maker = GifMaker()

        maker.make_gif(photoset.path / "gif", photoset.name)
