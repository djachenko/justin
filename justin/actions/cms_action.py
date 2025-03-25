from argparse import Namespace, ArgumentParser
from pathlib import Path
from typing import List

from justin.shared.context import Context
from justin.shared.metafile import MetaFolder
from justin.shared.models.photoset import Photoset
from justin_utils.cli import Action, Parameter


class CMSIndexAction(Action):

    def __init__(self) -> None:
        super().__init__()

    def configure_subparser(self, subparser: ArgumentParser) -> None:
        super().configure_subparser(subparser)

        group = subparser.add_mutually_exclusive_group(required=True)

        group.add_argument("--group")
        group.add_argument("--photoset")
        group.add_argument("--folder")

    def perform(self, args: Namespace, context: Context) -> None:
        if args.group:
            context.sqlite_cms.index_group(args.group, context.pyvko)
        elif args.photoset:
            photoset = Photoset.from_path(Path(args.photoset))

            context.sqlite_cms.index_photoset(photoset)
        elif args.folder:
            context.sqlite_cms.index_folder(MetaFolder.from_path(Path(args.folder)))
