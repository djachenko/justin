from argparse import ArgumentParser

from justin.actions.action import Action
from justin.actions.named.named_action import Context
from justin.actions.rearrange_action import RearrangeAction
from justin.commands.single_subparser_commands.single_subparser_command import SingleSubparserCommand


class UploadCommand(SingleSubparserCommand):
    def __init__(self, actions: [Action]) -> None:
        super().__init__()

        self.__actions = actions

    def command(self) -> str:
        return "upload"

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

        subparser.add_argument("-s", "--step", default=RearrangeAction.DEFAULT_STEP, type=int)
        subparser.add_argument("--shuffle", action="store_true")
        subparser.add_argument("name", nargs="+")  # todo: move to namedCommand

    def run(self, args, context: Context) -> None:
        for action in self.__actions:
            action.perform(args, context)
