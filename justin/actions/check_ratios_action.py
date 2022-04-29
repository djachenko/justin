from argparse import Namespace
from collections import defaultdict
from pathlib import Path
from typing import List

from PIL import Image

from justin.actions.named.named_action import Extra
from justin.actions.pattern_action import PatternAction
from justin_utils.cli import Context, Parameter


class CheckRatiosAction(PatternAction):

    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter(flags=["-v", "--verbose"], action=Parameter.Action.STORE_TRUE)
        ]

    def perform_for_path(self, path: Path, args: Namespace, context: Context, extra: Extra) -> None:
        ratios = defaultdict(lambda: [])

        for img_path in path.iterdir():
            with Image.open(img_path) as image:
                ratio = image.width / image.height

                ratio = round(ratio, 3)

                ratios[ratio].append(img_path.name)

        if args.verbose:
            for k, v in ratios.items():
                print(k, len(v), v)
        else:
            sorted_by_count = sorted(ratios.values(), key=len, reverse=True)
            minority_ratios = sorted_by_count[1:]

            if not minority_ratios:
                print("All good.")

                return

            for ratio in minority_ratios:
                print(", ".join(ratio))

