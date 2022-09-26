from functools import lru_cache

from justin.actions.action import Action
from justin.actions.check_ratios_action import CheckRatiosAction
from justin.actions.create_event_action import CreateEventAction, SetupEventAction
from justin.actions.date_split import DateSplitAction
from justin.actions.delay_action import DelayAction
from justin.actions.delete_posts_action import DeletePostsAction
from justin.actions.move_action import MoveAction
from justin.actions.named.fix_metafile_action import FixMetafileAction
from justin.actions.named.make_gifs_action import MakeGifAction
from justin.actions.named.resize_gif_sources_action import ResizeGifSourcesAction
from justin.actions.named.split_action import SplitAction
from justin.actions.named.stage.logic.factories.checks_factory import ChecksFactory
from justin.actions.named.stage.models.stages_factory import StagesFactory
from justin.actions.named.stage.stage_action import StageAction
from justin.actions.named.upload_action import UploadAction
from justin.actions.named.web_sync_action import WebSyncAction
from justin.actions.rearrange_action import RearrangeAction
from justin.actions.scheduled.local_sync_action import LocalSyncAction
from justin.actions.sequence_action import SequenceAction
from justin_utils.cli import Action as CLIAction


class ActionFactory:

    def __init__(self, stages_factory: StagesFactory, checks_factory: ChecksFactory) -> None:
        super().__init__()

        self.__stages_factory = stages_factory
        self.__checks_factory = checks_factory

    @lru_cache()
    def stage_action(self) -> Action:
        return StageAction(self.__stages_factory)

    @lru_cache()
    def local_sync_action(self) -> Action:
        return LocalSyncAction(
            prechecks=[self.__checks_factory.metafile()],
            all_published_action=self.stage_action()
        )


    @lru_cache()
    def move_action(self) -> CLIAction:
        return MoveAction(
            prechecks=[self.__checks_factory.metadata()]
        )

    @lru_cache()
    def make_gif_action(self) -> CLIAction:
        return MakeGifAction()

    @lru_cache()
    def split_action(self) -> CLIAction:
        return SplitAction()

    @lru_cache()
    def fix_metafile_action(self) -> CLIAction:
        return FixMetafileAction()

    @lru_cache()
    def web_sync_action(self) -> CLIAction:
        return WebSyncAction()

    @lru_cache()
    def delete_posts_action(self) -> CLIAction:
        return DeletePostsAction()

    @lru_cache()
    def rearrange_action(self) -> CLIAction:
        return RearrangeAction()

    @lru_cache()
    def delay_action(self) -> CLIAction:
        return DelayAction()

    @lru_cache()
    def resize_gif_action(self) -> CLIAction:
        return ResizeGifSourcesAction()

    @lru_cache()
    def upload_action(self) -> CLIAction:
        return UploadAction(
            create=self.create_event(),
            setup=self.setup_event()
        )

    @lru_cache()
    def check_ratios(self) -> CLIAction:
        return CheckRatiosAction()

    @lru_cache()
    def sequence(self) -> CLIAction:
        return SequenceAction()

    @lru_cache()
    def create_event(self) -> CreateEventAction:
        return CreateEventAction()

    @lru_cache()
    def setup_event(self) -> SetupEventAction:
        return SetupEventAction()

    @lru_cache()
    def date_split(self) -> CLIAction:
        return DateSplitAction()
