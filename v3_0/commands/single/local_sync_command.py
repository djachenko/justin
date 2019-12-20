from argparse import ArgumentParser

from v3_0.commands.single.single_subparser_command import SingleSubparserCommand
from v3_0.shared.justin import Justin


class LocalSyncCommand(SingleSubparserCommand):
    @classmethod
    def command(cls) -> str:
        return "local_sync"

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)

    def run(self, args, justin: Justin) -> None:
        justin.local_sync(args)
