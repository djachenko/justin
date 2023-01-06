from argparse import ArgumentParser
from typing import Iterable

from justin_utils.cli import Command, Action


class SingleActionCommand(Command):
    def __init__(self, name: str, action: Action, allowed_same_parameters: Iterable[str] = ()) -> None:
        super().__init__(name, [action], allowed_same_parameters)


class StageCommand(SingleActionCommand):
    def configure_subparser(self, subparser: ArgumentParser) -> None:
        super().configure_subparser(subparser)

        subparser.set_defaults(command_name=self.name)
