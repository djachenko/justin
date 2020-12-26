from argparse import Namespace

from pyvko.models.group import Group

from justin.actions.named.named_action import NamedAction
from justin.shared.helpers.gif_maker import GifMaker
from justin.shared.models.photoset import Photoset
from justin.shared.models.world import World


class ResizeGifSourcesAction(NamedAction):
    def perform_for_photoset(self, photoset: Photoset, args: Namespace, world: World, group: Group) -> None:
        maker = GifMaker()

        factor = args.factor

        maker.resize_sources(photoset.path / "gif", scale_factor=factor)
