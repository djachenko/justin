from argparse import ArgumentParser

from justin.actions.action_id import ActionId
from justin.actions.rearrange_action import RearrangeAction
from justin.commands.single_subparser_commands.single_subparser_command import SingleSubparserCommand
from justin.shared.justin import Justin


class UploadCommand(SingleSubparserCommand):
    def command(self) -> str:
        return "upload"

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

        subparser.add_argument("-s", "--step", default=RearrangeAction.DEFAULT_STEP, type=int)
        subparser.add_argument("--shuffle", action="store_true")
        subparser.add_argument("name", nargs="+")  # move to namedCommand

    def run(self, args, justin: Justin) -> None:
        actions = [
            ActionId.SYNC_POSTS_STATUS,
            ActionId.SCHEDULE,
            ActionId.REARRANGE
        ]

        for action in actions:
            justin[action](args)
