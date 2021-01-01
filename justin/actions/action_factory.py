from functools import lru_cache

from justin.actions.action import Action
from justin.actions.action_id import ActionId
from justin.actions.delay_action import DelayAction
from justin.actions.delete_posts_action import DeletePostsAction
from justin.actions.named.archive_action import ArchiveAction
from justin.actions.named.fix_metafile_action import FixMetafileAction
from justin.actions.named.make_gifs_action import MakeGifAction
from justin.actions.move_action import MoveAction
from justin.actions.named.resize_gif_sources_action import ResizeGifSourcesAction
from justin.actions.named.split_action import SplitAction
from justin.actions.named.stage.logic.factories.checks_factory import ChecksFactory
from justin.actions.named.stage.models.stages_factory import StagesFactory
from justin.actions.named.stage.stage_action import StageAction
from justin.actions.rearrange_action import RearrangeAction
from justin.actions.scheduled.local_sync_action import LocalSyncAction
from justin.actions.named.schedule_action import ScheduleAction
from justin.actions.named.web_sync_action import WebSyncAction


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
        ActionId.SYNC_POSTS_STATUS: WebSyncAction,
        ActionId.SPLIT: SplitAction,
        ActionId.FIX_METAFILE: FixMetafileAction,
        ActionId.DELAY: DelayAction,
        ActionId.RESIZE_SOURCES: ResizeGifSourcesAction,
    }

    def __init__(self, stages_factory: StagesFactory, checks_factory: ChecksFactory) -> None:
        super().__init__()

        self.__parameters_mapping = {
            ActionId.STAGE: lambda: [stages_factory],
            ActionId.LOCAL_SYNC: lambda: [[checks_factory.metafile()], self.__get(ActionId.STAGE)],
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
