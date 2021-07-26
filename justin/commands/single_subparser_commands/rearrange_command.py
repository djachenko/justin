from argparse import ArgumentParser

from justin.actions.action import Action
from justin.actions.rearrange_action import RearrangeAction
from justin.commands.single_subparser_commands.single_action_command import SingleActionCommand


class RearrangeCommand(SingleActionCommand):
    def __init__(self, action: Action) -> None:
        super().__init__("rearrange", action)

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

        subparser.add_argument("-s", "--step", default=RearrangeAction.DEFAULT_STEP, type=int)
        subparser.add_argument("--shuffle", action="store_true")
