from argparse import Namespace

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.shared.models.photoset import Photoset


class ResizeGifSourcesAction(NamedAction):

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        maker = context.gif_maker

        factor = args.factor

        maker.resize_sources(part.path / "gif", scale_factor=factor)
