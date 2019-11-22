from argparse import ArgumentParser

from v3_0.commands.command import Command
from v3_0.shared.justin import Justin


class ArchiveCommand(Command):
    __COMMAND = "archive"

    def configure_parser(self, parser_adder):
        subparser: ArgumentParser = parser_adder.add_parser(self.__COMMAND)

        subparser.add_argument("patterns", nargs="+")

        self.setup_callback(subparser)

    def run(self, args, justin: Justin) -> None:
        justin.archive(args)
