from abc import abstractmethod
from argparse import ArgumentParser, Namespace

from v3_0.shared.justin import Justin


class Command:
    @abstractmethod
    def run(self, args: Namespace, justin: Justin) -> None:
        pass

    @abstractmethod
    def configure_parser(self, parser_adder):
        pass

    def setup_callback(self, parser: ArgumentParser):
        parser.set_defaults(func=self.run)
