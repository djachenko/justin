from argparse import Namespace, ArgumentParser

from v3_0.commands.command import Command
from v3_0.shared.justin import Justin


class MoveCommand(Command):
    def run(self, args: Namespace, justin: Justin) -> None:
        justin.move(args)

    def configure_parser(self, parser_adder):
        command = "move"

        subparser: ArgumentParser = parser_adder.add_parser(command)

        subparser.add_argument("name", nargs="+")

        self.setup_callback(subparser)
