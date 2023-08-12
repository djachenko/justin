from argparse import Namespace
from collections import defaultdict
from typing import List, Tuple, Dict

from PIL import Image

from justin.actions.pattern_action import PatternAction, Extra
from justin.shared.filesystem import Folder, File
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

    def perform_for_folder(self, folder: Folder, args: Namespace, context: Context, extra: Extra) -> None:
        ratios: Dict[float, List[File]] = defaultdict(lambda: [])

        precision = args.precision

        for img in sorted(folder.files):
            with Image.open(img.path) as image:
                ratio = image.width / image.height

                ratio = round(ratio, precision)

                ratios[ratio].append(img)

        if args.verbose:
            for k, v in ratios.items():
                print(f"{k}, {len(v)}: ", end="")

                print(", ".join([image.name for image in v]))
        else:
            sorted_by_count = sorted(
                ratios.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )

            minority_ratios = sorted_by_count[1:]

            if not minority_ratios:
                print("All good.")

                return

            for ratio, images in minority_ratios:
                print(f"{ratio}: ", end="")
                print(", ".join([image.name for image in images]))

            if args.extract:
                for ratio, image_list in minority_ratios:
                    ratio_subfolder = folder / f"{ratio}"

                    ratio_subfolder.mkdir()

                    print(image_list)

                    for image in image_list:
                        image.rename(ratio_subfolder.path / image.name)
