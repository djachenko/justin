from functools import lru_cache

from v3_0.actions.action import Action
from v3_0.actions.archive.archive_action import ArchiveAction
from v3_0.actions.delete_posts_action import DeletePostsAction
from v3_0.actions.local_sync_action import LocalSyncAction
from v3_0.actions.move_action import MoveAction
from v3_0.actions.rearrange.rearrange_action import RearrangeAction
from v3_0.actions.schedule.schedule_action import ScheduleAction
from v3_0.actions.stage.logic.factories.checks_factory import ChecksFactory
from v3_0.actions.stage.models.stages_factory import StagesFactory
from v3_0.actions.stage.stage_action import StageAction
from v3_0.actions.sync_posts_status_action import SyncPostsStatusAction


class ActionFactory:

    def __init__(self, stages_factory: StagesFactory, checks_factory: ChecksFactory) -> None:
        super().__init__()

        self.__stages_factory = stages_factory
        self.__checks_factory = checks_factory

    @lru_cache()
    def stage(self) -> Action:
        return StageAction(self.__stages_factory)

    @lru_cache()
    def schedule(self) -> Action:
        return ScheduleAction()

    @lru_cache()
    def rearrange(self) -> Action:
        return RearrangeAction()

    @lru_cache()
    def sync_posts_status(self) -> Action:
        return SyncPostsStatusAction()

    @lru_cache()
    def delete_posts(self) -> Action:
        return DeletePostsAction()

    @lru_cache()
    def local_sync(self) -> Action:
        return LocalSyncAction(self.stage())

    @lru_cache()
    def archive(self) -> Action:
        return ArchiveAction()

    @lru_cache()
    def move(self) -> Action:
        return MoveAction([
            self.__checks_factory.metadata(),
        ])
