from argparse import Namespace, ArgumentParser

from v3_0.commands.single.single_subparser_command import SingleSubparserCommand
from v3_0.shared.justin import Justin


class DeletePostsCommand(SingleSubparserCommand):
    @classmethod
    def command(cls) -> str:
        return "delete_posts"

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

        subparser.add_argument("--published", action="store_true")

    def run(self, args: Namespace, justin: Justin) -> None:
        justin.delete_posts(args)
