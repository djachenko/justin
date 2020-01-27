from functools import lru_cache

from v3_0.actions.action import Action
from v3_0.actions.action_id import ActionId
from v3_0.actions.archive.archive_action import ArchiveAction
from v3_0.actions.delete_posts_action import DeletePostsAction
from v3_0.actions.fix_metafile_action import FixMetafileAction
from v3_0.actions.local_sync_action import LocalSyncAction
from v3_0.actions.make_gif.make_gifs_action import MakeGifAction
from v3_0.actions.move_action import MoveAction
from v3_0.actions.rearrange.rearrange_action import RearrangeAction
from v3_0.actions.schedule.schedule_action import ScheduleAction
from v3_0.actions.split_action import SplitAction
from v3_0.actions.stage.logic.factories.checks_factory import ChecksFactory
from v3_0.actions.stage.models.stages_factory import StagesFactory
from v3_0.actions.stage.stage_action import StageAction
from v3_0.actions.sync_posts_status_action import SyncPostsStatusAction


class ActionFactory:
    __TYPES_MAPPING = {
        ActionId.ARCHIVE: ArchiveAction,
        ActionId.DELETE_POSTS: DeletePostsAction,
        ActionId.LOCAL_SYNC: LocalSyncAction,
        ActionId.MAKE_GIF: MakeGifAction,
        ActionId.MOVE: MoveAction,
        ActionId.REARRANGE: RearrangeAction,
        ActionId.SCHEDULE: ScheduleAction,
        ActionId.STAGE: StageAction,
        ActionId.SYNC_POSTS_STATUS: SyncPostsStatusAction,
        ActionId.SPLIT: SplitAction,
        ActionId.FIX_METAFILE: FixMetafileAction,
    }

    def __init__(self, stages_factory: StagesFactory, checks_factory: ChecksFactory) -> None:
        super().__init__()

        self.__parameters_mapping = {
            ActionId.STAGE: lambda: [stages_factory],
            ActionId.LOCAL_SYNC: lambda: [self.__get(ActionId.STAGE)],
            ActionId.MOVE: lambda: [[checks_factory.metadata()]],
        }

    # noinspection PyTypeChecker
    @lru_cache(len(ActionId))
    def __get(self, identifier: ActionId) -> Action:
        action_type = ActionFactory.__TYPES_MAPPING[identifier]
        parameters_generator = self.__parameters_mapping.get(identifier, lambda: [])

        parameters = parameters_generator()

        action = action_type(*parameters)

        return action

    def __getitem__(self, item: ActionId) -> Action:
        return self.__get(item)
