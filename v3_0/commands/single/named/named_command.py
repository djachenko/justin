from abc import ABC
from argparse import ArgumentParser

from v3_0.commands.single.single_subparser_command import SingleSubparserCommand


class NamedCommand(SingleSubparserCommand, ABC):
    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

        subparser.add_argument("name", nargs="+")
