from argparse import ArgumentParser

from v3_0.actions.rearrange.rearrange_action import RearrangeAction
from v3_0.commands.command import Command
from v3_0.shared.justin import Justin


class UploadCommand(Command):
    __COMMAND = "upload"

    def configure_parser(self, parser_adder):
        subparser: ArgumentParser = parser_adder.add_parser(UploadCommand.__COMMAND)

        subparser.add_argument("-s", "--step", default=RearrangeAction.DEFAULT_STEP, type=int)

        self.setup_callback(subparser)

    def run(self, args, justin: Justin) -> None:
        justin.sync_posts_status(args)
        justin.schedule(args)
        justin.rearrange(args)
