from argparse import Namespace, ArgumentParser

from v3_0.commands.command import Command
from v3_0.shared.justin import Justin


class DeletePostsCommand(Command):
    __COMMAND = "delete_posts"

    def configure_parser(self, parser_adder):
        subparser: ArgumentParser = parser_adder.add_parser(DeletePostsCommand.__COMMAND)

        subparser.add_argument("--published", action="store_true")

        self.setup_callback(subparser)

    def run(self, args: Namespace, justin: Justin) -> None:
        justin.delete_posts(args)
