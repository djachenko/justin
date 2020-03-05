from abc import ABC, abstractmethod
from argparse import ArgumentParser

from v3_0.commands.command import Command


class SingleSubparserCommand(Command, ABC):
    @abstractmethod
    def command(self) -> str:
        pass

    def configure_parser(self, parser_adder):
        subparser: ArgumentParser = parser_adder.add_parser(self.command())

        self.configure_subparser(subparser)

        self.setup_callback(subparser)

    @abstractmethod
    def configure_subparser(self, subparser: ArgumentParser):
        pass
