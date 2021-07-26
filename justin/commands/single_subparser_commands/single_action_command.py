from argparse import Namespace, ArgumentParser

from justin.actions.action_id import ActionId
from justin.commands.single_subparser_commands.single_subparser_command import SingleSubparserCommand
from justin.shared.justin import Justin


class SingleActionCommand(SingleSubparserCommand):
    def __init__(self, command: str, action: ActionId) -> None:
        super().__init__()

        self.__command = command
        self.__action = action

    def command(self) -> str:
        return self.__command

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

    def run(self, args: Namespace, justin: Justin) -> None:
        justin[self.__action](args)