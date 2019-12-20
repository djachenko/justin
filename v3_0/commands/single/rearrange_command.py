from argparse import ArgumentParser

from v3_0.actions.rearrange.rearrange_action import RearrangeAction
from v3_0.commands.single.single_subparser_command import SingleSubparserCommand
from v3_0.shared.justin import Justin


class RearrangeCommand(SingleSubparserCommand):
    @classmethod
    def command(cls) -> str:
        return "rearrange"

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

        subparser.add_argument("-s", "--step", default=RearrangeAction.DEFAULT_STEP, type=int)

    def run(self, args, justin: Justin) -> None:
        justin.rearrange(args)
