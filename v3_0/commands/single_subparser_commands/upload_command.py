from argparse import ArgumentParser

from v3_0.actions.action_id import ActionId
from v3_0.actions.rearrange_action import RearrangeAction
from v3_0.commands.single_subparser_commands.single_subparser_command import SingleSubparserCommand
from v3_0.shared.justin import Justin


class UploadCommand(SingleSubparserCommand):
    def command(self) -> str:
        return "upload"

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

        subparser.add_argument("-s", "--step", default=RearrangeAction.DEFAULT_STEP, type=int)

    def run(self, args, justin: Justin) -> None:
        justin[ActionId.SYNC_POSTS_STATUS](args)
        justin[ActionId.SCHEDULE](args)
        justin[ActionId.REARRANGE](args)
