from functools import lru_cache

from justin.actions.check_ratios_action import CheckRatiosAction
from justin.actions.date_split import DateSplitAction
from justin.actions.delay_action import DelayAction
from justin.actions.delete_posts_action import DeletePostsAction
from justin.actions.drone import HandleDroneAction, JpgDngDuplicatesAction, PanoExtractAction
from justin.actions.event import SetupEventAction, CreateEventAction
from justin.actions.location import LocationAction
from justin.actions.move_action import MoveAction
from justin.actions.fix_metafile_action import FixMetafileAction
from justin.actions.make_gifs_action import MakeGifAction
from justin.actions.resize_gif_sources_action import ResizeGifSourcesAction
from justin.actions.split_action import SplitAction
from justin.actions.stage.stage_action import StageAction
from justin.actions.upload_action import UploadAction
from justin.actions.web_sync_action import WebSyncAction
from justin.actions.people import FixPeopleAction, RegisterPeopleAction
from justin.actions.rearrange_action import RearrangeAction
from justin.actions.sequence_action import SequenceAction
from justin.cms.cms import CMSAction
from justin.di.checks import ChecksFactory
from justin.di.stages import StagesFactory
from justin.shared.helpers.checks_runner import ChecksRunner
from justin_utils.cli import Action


class ActionFactory:
    def __init__(self, stages_factory: StagesFactory, checks_factory: ChecksFactory, checks_runner: ChecksRunner) \
            -> None:
        super().__init__()

        self.__stages_factory = stages_factory
        self.__checks_factory = checks_factory
        self.__runner = checks_runner

    @lru_cache()
    def stage_action(self) -> Action:
        return StageAction(self.__stages_factory)

    @lru_cache()
    def move_action(self) -> Action:
        return MoveAction(
            prechecks=[self.__checks_factory.metadata()],
            runner=self.__runner
        )

    @lru_cache()
    def make_gif_action(self) -> Action:
        return MakeGifAction()

    @lru_cache()
    def split_action(self) -> Action:
        return SplitAction()

    @lru_cache()
    def fix_metafile_action(self) -> Action:
        return FixMetafileAction()

    @lru_cache()
    def web_sync_action(self) -> Action:
        return WebSyncAction()

    @lru_cache()
    def delete_posts_action(self) -> Action:
        return DeletePostsAction()

    @lru_cache()
    def rearrange_action(self) -> Action:
        return RearrangeAction()

    @lru_cache()
    def delay_action(self) -> Action:
        return DelayAction()

    @lru_cache()
    def resize_gif_action(self) -> Action:
        return ResizeGifSourcesAction()

    @lru_cache()
    def upload_action(self) -> Action:
        return UploadAction(
            setup=self.setup_event()
        )

    @lru_cache()
    def check_ratios(self) -> Action:
        return CheckRatiosAction()

    @lru_cache()
    def sequence(self) -> Action:
        return SequenceAction()

    @lru_cache()
    def create_event(self) -> Action:
        return CreateEventAction()

    @lru_cache()
    def setup_event(self) -> SetupEventAction:
        return SetupEventAction()

    @lru_cache()
    def date_split(self) -> Action:
        return DateSplitAction()

    @lru_cache()
    def register_people(self) -> Action:
        return RegisterPeopleAction()

    @lru_cache()
    def __pano_extract(self) -> PanoExtractAction:
        return PanoExtractAction()

    @lru_cache()
    def __deduplicate(self) -> JpgDngDuplicatesAction:
        return JpgDngDuplicatesAction()

    @lru_cache()
    def drone(self) -> Action:
        return HandleDroneAction(
            pano_action=self.__pano_extract(),
            duplicate_action=self.__deduplicate(),
        )

    @lru_cache()
    def fix_people(self) -> Action:
        return FixPeopleAction()

    @lru_cache()
    def cms(self) -> Action:
        return CMSAction()

    @lru_cache()
    def location(self) -> Action:
        return LocationAction()
