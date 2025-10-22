from functools import cache

from justin.actions.attach_album_action import AttachAlbumAction2
from justin.actions.check_ratios_action import CheckRatiosAction
from justin.actions.cms_action import CMSIndexAction
from justin.actions.date_split import DateSplitAction
from justin.actions.delay_action import DelayAction
from justin.actions.delete_posts_action import DeletePostsAction
from justin.actions.drone import HandleDroneAction, JpgDngDuplicatesAction, PanoExtractAction
from justin.actions.event import SetupEventAction, CreateEventAction
from justin.actions.fix_metafile_action import FixMetafileAction
from justin.actions.get_likers_action import GetLikersAction
from justin.actions.location import LocationAction
from justin.actions.manage_tags_action import ManageTagsAction
from justin.actions.move_action import MoveAction
from justin.actions.people import RegisterPeopleAction, FixPeopleAction, SpecifyPersonAction
from justin.actions.populate_action import PopulateAction
from justin.actions.rearrange_action import RearrangeAction
from justin.actions.sequence_action import SequenceAction
from justin.actions.split_action import SplitAction
from justin.actions.stage.stage_action import StageAction
from justin.actions.step_sources_action import StepSourcesAction
from justin.actions.upload_action import UploadAction
from justin.actions.web_sync_action import WebSyncAction
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

    @cache
    def stage_action(self) -> Action:
        return StageAction(
            factory=self.__stages_factory,
            checks_runner=self.__runner
        )

    @cache
    def move_action(self) -> Action:
        return MoveAction(
            prechecks=[self.__checks_factory.metadata()],
            runner=self.__runner
        )

    @cache
    def split_action(self) -> Action:
        return SplitAction()

    @cache
    def fix_metafile_action(self) -> Action:
        return FixMetafileAction()

    @cache
    def web_sync_action(self) -> Action:
        return WebSyncAction()

    @cache
    def delete_posts_action(self) -> Action:
        return DeletePostsAction()

    @cache
    def rearrange_action(self) -> Action:
        return RearrangeAction()

    @cache
    def delay_action(self) -> Action:
        return DelayAction()

    @cache
    def upload_action(self) -> Action:
        return UploadAction(
            setup=self.setup_event()
        )

    @cache
    def check_ratios(self) -> Action:
        return CheckRatiosAction()

    @cache
    def sequence(self) -> Action:
        return SequenceAction()

    @cache
    def create_event(self) -> Action:
        return CreateEventAction()

    @cache
    def setup_event(self) -> SetupEventAction:
        return SetupEventAction()

    @cache
    def date_split(self) -> Action:
        return DateSplitAction()

    @cache
    def register_people(self) -> Action:
        return RegisterPeopleAction()

    @cache
    def __pano_extract(self) -> PanoExtractAction:
        return PanoExtractAction()

    @cache
    def __deduplicate(self) -> JpgDngDuplicatesAction:
        return JpgDngDuplicatesAction()

    @cache
    def drone(self) -> Action:
        return HandleDroneAction(
            pano_action=self.__pano_extract(),
            duplicate_action=self.__deduplicate(),
        )

    @cache
    def fix_people(self) -> Action:
        return FixPeopleAction()

    @cache
    def migrate_person(self) -> Action:
        return SpecifyPersonAction()

    @cache
    def location(self) -> Action:
        return LocationAction()

    @cache
    def cms_index(self) -> Action:
        return CMSIndexAction()

    @cache
    def attach_album(self) -> Action:
        return AttachAlbumAction2()

    @cache
    def get_likers(self) -> Action:
        return GetLikersAction()

    @cache
    def manage_tags(self) -> Action:
        return ManageTagsAction()

    @cache
    def populate(self) -> Action:
        return PopulateAction()

    @cache
    def step_sources(self) -> Action:
        return StepSourcesAction()
