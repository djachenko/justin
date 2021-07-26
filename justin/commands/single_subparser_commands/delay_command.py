from argparse import ArgumentParser

from justin.actions.action_id import ActionId
from justin.actions.delay_action import DelayAction
from justin.commands.single_subparser_commands.single_action_command import SingleActionCommand


class DelayCommand(SingleActionCommand):
    def __init__(self) -> None:
        super().__init__("delay", ActionId.DELAY)

    def configure_subparser(self, subparser: ArgumentParser):
        subparser.add_argument("-d", "--days", default=DelayAction.DEFAULT_DAYS, type=int)
