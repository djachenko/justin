from abc import ABC
from argparse import ArgumentParser

from v3_0.commands.single_subparser_commands.single_action_command import SingleActionCommand


class NamedCommand(SingleActionCommand, ABC):
    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

        subparser.add_argument("name", nargs="+")
