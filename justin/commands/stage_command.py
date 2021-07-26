from argparse import ArgumentParser, Namespace

from justin.actions.action_id import ActionId
from justin.actions.named.stage.models.stages_factory import StagesFactory
from justin.commands.command import Command
from justin.shared.justin import Justin


class StageCommand(Command):
    def __init__(self, factory: StagesFactory) -> None:
        super().__init__()

        self.__stages_factory = factory

    def configure_parser(self, parser_adder):
        for stage in self.__stages_factory.stages():
            command = stage.command

            subparser: ArgumentParser = parser_adder.add_parser(command)

            subparser.add_argument("name", nargs="+")
            subparser.set_defaults(command=command)

            self.setup_callback(subparser)

    def run(self, args: Namespace, justin: Justin) -> None:
        justin[ActionId.STAGE](args)
