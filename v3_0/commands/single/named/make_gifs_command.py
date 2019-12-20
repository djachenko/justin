from argparse import Namespace

from v3_0.commands.single.named.named_command import NamedCommand
from v3_0.shared.justin import Justin


class MakeGifCommand(NamedCommand):
    @classmethod
    def command(cls) -> str:
        return "make_gif"

    def run(self, args: Namespace, justin: Justin) -> None:
        justin.make_gif(args)
