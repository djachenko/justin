from argparse import ArgumentParser

from v3_0.actions.action_id import ActionId
from v3_0.commands.single_subparser_commands.single_action_command import SingleActionCommand


class LocalSyncCommand(SingleActionCommand):
    def __init__(self) -> None:
        super().__init__("local_sync", ActionId.LOCAL_SYNC)

    def configure_subparser(self, subparser: ArgumentParser):
        super().configure_subparser(subparser)
