from argparse import ArgumentParser

from justin.actions.action_id import ActionId
from justin.commands.single_subparser_commands.single_action_command import SingleActionCommand


class DeletePostsCommand(SingleActionCommand):
    def __init__(self) -> None:
        super().__init__("delete_posts", ActionId.DELETE_POSTS)

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

        subparser.add_argument("--published", action="store_true")
