from argparse import ArgumentParser

from v3_0.commands.command import Command
from v3_0.shared.justin import Justin


class LocalSyncCommand(Command):
    __COMMAND = "local_sync"

    def configure_parser(self, parser_adder):
        subparser: ArgumentParser = parser_adder.add_parser(LocalSyncCommand.__COMMAND)

        self.setup_callback(subparser)

    def run(self, args, justin: Justin) -> None:
        justin.local_sync(args)
