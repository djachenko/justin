from argparse import ArgumentParser

from v3_0.actions.action_id import ActionId
from v3_0.actions.rearrange_action import RearrangeAction
from v3_0.commands.single_subparser_commands.single_action_command import SingleActionCommand


class RearrangeCommand(SingleActionCommand):
    def __init__(self) -> None:
        super().__init__("rearrange", ActionId.REARRANGE)

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

        subparser.add_argument("-s", "--step", default=RearrangeAction.DEFAULT_STEP, type=int)
