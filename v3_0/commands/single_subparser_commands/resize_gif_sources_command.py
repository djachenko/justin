from argparse import ArgumentParser

from v3_0.actions.action_id import ActionId
from v3_0.commands.single_subparser_commands.named_command import NamedCommand


class ResizeGifSourcesCommand(NamedCommand):
    def __init__(self, ) -> None:
        super().__init__("resize_gif_sources", ActionId.RESIZE_SOURCES)

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

        subparser.add_argument("-f", "--factor", type=float)
