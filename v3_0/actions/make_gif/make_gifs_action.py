from argparse import Namespace

from pyvko.models.group import Group

from v3_0.actions.action import Action
from v3_0.actions.stage.helpers.gif_maker import GifMaker
from v3_0.shared.helpers import util
from v3_0.shared.models.world import World


class MakeGifAction(Action):
    def perform(self, args: Namespace, world: World, group: Group) -> None:
        maker = GifMaker()

        for path in util.resolve_patterns(args.name):
            maker.make_gif(path / "gif", path.name)
