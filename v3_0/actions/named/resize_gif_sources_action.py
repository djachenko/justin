from argparse import Namespace

from pyvko.models.group import Group

from v3_0.actions.named.named_action import NamedAction
from v3_0.shared.helpers.gif_maker import GifMaker
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class ResizeGifSourcesAction(NamedAction):
    def perform_for_photoset(self, photoset: Photoset, args: Namespace, world: World, group: Group) -> None:
        maker = GifMaker()

        factor = args.factor

        maker.resize_sources(photoset.path / "gif", scale_factor=factor)
