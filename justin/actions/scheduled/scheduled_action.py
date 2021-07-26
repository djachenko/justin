from abc import ABC

from justin.actions.action import Action
from justin.shared.filesystem import FolderTree
from justin.shared.models.world import World


class ScheduledAction(Action, ABC):
    # noinspection PyMethodMayBeStatic
    def tree_with_sets(self, world: World) -> FolderTree:
        # todo: stages_region[stage3.schedule]
        scheduled_path = world.current_location / "stages/stage3.schedule"

        stage_tree = FolderTree(scheduled_path)

        return stage_tree
