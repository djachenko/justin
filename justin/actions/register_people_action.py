from argparse import Namespace
from pathlib import Path

from justin.actions.named.destinations_aware_action import DestinationsAwareAction
from justin.actions.named.named_action import Extra
from justin.shared.context import Context


class RegisterPeopleAction(DestinationsAwareAction):
    def perform_for_path(self, path: Path, args: Namespace, context: Context, extra: Extra) -> None:
        context.my_people.register(path)
        context.closed.register(path)
