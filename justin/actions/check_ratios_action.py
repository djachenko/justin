from argparse import Namespace
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from justin.actions.named.named_action import Extra
from justin.actions.pattern_action import PatternAction
from justin_utils.cli import Context, Parameter


class CheckRatiosAction(PatternAction):
    __DEFAULT_PRECISION = 3

    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter(flags=["-v", "--verbose"], action=Parameter.Action.STORE_TRUE),
            Parameter(flags=["-e", "--extract"], action=Parameter.Action.STORE_TRUE),
            Parameter(flags=["-p", "--precision"], type=int, default=CheckRatiosAction.__DEFAULT_PRECISION),
        ]

    def perform_for_path(self, path: Path, args: Namespace, context: Context, extra: Extra) -> None:
        ratios = defaultdict(lambda: [])

        precision = args.precision

        for img_path in sorted(filter(lambda x: x.is_file(), path.iterdir())):
            with Image.open(img_path) as image:
                ratio = image.width / image.height

                ratio = round(ratio, precision)

                ratios[ratio].append(img_path)

        if args.verbose:
            for k, v in ratios.items():
                print(k, len(v), v)
        else:
            sorted_by_count: List[Tuple[float, List[Path]]] = sorted(ratios.items(), key=lambda x: len(x[1]), reverse=True)
            minority_ratios = sorted_by_count[1:]

            if not minority_ratios:
                print("All good.")

                return

            for ratio, images in minority_ratios:
                print(f"{ratio}: ", end="")
                print(", ".join([image.name for image in images]))

            if args.extract:
                for ratio, image_list in minority_ratios:
                    ratio_subfolder = path / f"{ratio}"

                    ratio_subfolder.mkdir(exist_ok=True)

                    print(image_list)

                    for image in image_list:
                        image.rename(ratio_subfolder / image.name)