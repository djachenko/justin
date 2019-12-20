from argparse import Namespace

from v3_0.commands.single.named.named_command import NamedCommand
from v3_0.shared.justin import Justin


class MoveCommand(NamedCommand):
    @classmethod
    def command(cls) -> str:
        return "move"

    def run(self, args: Namespace, justin: Justin) -> None:
        justin.move(args)
