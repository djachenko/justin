from abc import abstractmethod
from argparse import ArgumentParser, Namespace

from justin.shared.context import Context


class Command:
    @abstractmethod
    def configure_parser(self, parser_adder):
        pass

    @abstractmethod
    def run(self, args: Namespace, context: Context) -> None:
        pass

    def setup_callback(self, parser: ArgumentParser):
        parser.set_defaults(func=self.run)
