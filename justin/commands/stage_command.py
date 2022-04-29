from argparse import ArgumentParser, Namespace

from justin.actions.action import Action
from justin.actions.named.stage.models.stages_factory import StagesFactory
from justin.commands.command import Command
from justin.shared.context import Context


class StageCommand(Command):
    def __init__(self, action: Action, factory: StagesFactory) -> None:
        super().__init__()

        self.__action = action
        self.__stages_factory = factory
        self.name = "stage"

    def configure_parser(self, parser_adder):
        for stage in self.__stages_factory.stages():
            command = stage.command

            subparser: ArgumentParser = parser_adder.add_parser(command)

            subparser.add_argument("name", nargs="+")
            subparser.set_defaults(command=command)

            self.setup_callback(subparser)

    def run(self, args: Namespace, context: Context) -> None:
        self.__action.perform(args, context)
