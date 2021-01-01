from argparse import Namespace
from typing import Optional

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.shared.models.photoset import Photoset


class MakeGifAction(NamedAction):
    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Optional[Extra]) -> None:
        maker = context.gif_maker

        maker.make_gif(part.path / "gif", part.name)
