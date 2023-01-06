from argparse import Namespace
from typing import List

from justin.actions.pattern_action import Context, Extra
from justin.actions.pattern_action import PatternAction
from justin.shared.models.photoset import Photoset
from justin_utils.cli import Parameter


class ResizeGifSourcesAction(PatternAction):
    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter(flags=["-f", "--factor"], type=float)
        ]

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        maker = context.gif_maker

        factor = args.factor

        maker.resize_sources(part.path / "gif", scale_factor=factor)
