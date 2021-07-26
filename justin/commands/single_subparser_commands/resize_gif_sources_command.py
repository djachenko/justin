from argparse import ArgumentParser

from justin.actions.action import Action
from justin.commands.single_subparser_commands.named_command import NamedCommand


class ResizeGifSourcesCommand(NamedCommand):
    def __init__(self, action: Action) -> None:
        super().__init__("resize_gif_sources", action)

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

        subparser.add_argument("-f", "--factor", type=float)
