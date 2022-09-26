from argparse import Namespace
from typing import Iterable, List

from justin.actions.action import Action
from justin.actions.named.stage.exceptions.check_failed_error import CheckFailedError
from justin.actions.named.stage.logic.base import Check
from justin.actions.scheduled.scheduled_action import ScheduledAction
from justin.shared.context import Context
from justin.shared.helpers.checks_runner import ChecksRunner
from justin.shared.models.photoset import Photoset


# todo: maybe just replace with publish *
class LocalSyncAction(ScheduledAction):
    def __init__(self, prechecks: List[Check], all_published_action: Action) -> None:
        super().__init__()

        self.__prechecks = prechecks
        self.__all_published_action = all_published_action

    def __check_for_publishing(self, photosets: Iterable[Photoset], context: Context):
        paths_of_published_sets = []

        for photoset in photosets:
            print(f"Syncing post {photoset.name}...")

            try:
                for part in photoset.parts:
                    ChecksRunner.instance().run_except(part, self.__prechecks)

                paths_of_published_sets.append(photoset.path)

                print("Scheduled to publish.")

            except CheckFailedError:
                print("Left as is.")

            print()

        if len(paths_of_published_sets) == 0:
            return

        input("Press Enter to proceed to publishing.")

        str_paths = [str(path.absolute()) for path in paths_of_published_sets]

        internal_args = Namespace(
            command="publish",
            name=str_paths
        )

        self.__all_published_action.perform(internal_args, context)

    def perform(self, args: Namespace, context: Context) -> None:
        stage_tree = self.tree_with_sets(context.world)

        photosets = [Photoset(subtree) for subtree in stage_tree.subtrees]

        self.__check_for_publishing(photosets, context)
