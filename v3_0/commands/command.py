from abc import abstractmethod
from argparse import ArgumentParser


class Command:
    @abstractmethod
    def run(self, args) -> None:
        pass

    @abstractmethod
    def configure_parser(self, parser_adder):
        pass

    def setup_callback(self, parser: ArgumentParser):
        parser.set_defaults(func=self.run)

