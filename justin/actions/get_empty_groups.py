from argparse import Namespace

from justin.shared.context import Context
from justin_utils.cli import Action


class GetEmptyEventsAction(Action):
    def perform(self, args: Namespace, context: Context) -> None:
        user = context.pyvko.current_user()

        user.groups()