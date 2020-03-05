from abc import ABC

from v3_0.actions.action import Action
from v3_0.shared.filesystem.folder_tree import FolderTree
from v3_0.shared.models.world import World


class ScheduledAction(Action, ABC):
    # noinspection PyMethodMayBeStatic
    def tree_with_sets(self, world: World) -> FolderTree:
        # todo: stages_region[stage3.schedule]
        scheduled_path = world.current_location / "stages/stage3.schedule"

        stage_tree = FolderTree(scheduled_path)

        return stage_tree
