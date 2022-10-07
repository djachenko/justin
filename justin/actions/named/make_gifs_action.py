from argparse import Namespace
from pathlib import Path
from typing import List

from justin.actions.pattern_action import Extra
from justin.actions.pattern_action import PatternAction
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.models.photoset import Photoset
from justin_utils.cli import Context, Parameter


class MakeGifAction(PatternAction):
    __SET_NAME = "set_name"

    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter("--min", type=int, default=None),
            Parameter("--max", type=int, default=None),
        ]

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        extra[MakeGifAction.__SET_NAME] = photoset.path

        super().perform_for_photoset(photoset, args, context, extra)

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        gif_path = part.path / "gif"
        frames_path = part.path / "frames"

        if not gif_path.exists():
            if frames_path.exists():
                frames_path.rename(gif_path)
            else:
                print("There is no sources folder.")

        set_path: Path = extra[MakeGifAction.__SET_NAME]
        set_name = set_path.name

        if part.name == set_name:
            gif_name = set_name
        else:
            gif_name = f"{set_name}_{part.name}"

        print(f"Making gif for {part.path.relative_to(set_path.parent)}")

        for gif_part in folder_tree_parts(part.gif):
            if gif_part == gif_path:
                gif_part_name = gif_name
            else:
                gif_part_name = f"{gif_name}_{gif_part.name}"

            context.gif_maker.make_gif(gif_part.path, gif_part_name, min_size=args.min, max_size=args.max)
