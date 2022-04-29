from argparse import Namespace

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.actions.named.stage.exceptions.check_failed_error import CheckFailedError
from justin.actions.named.stage.logic.exceptions.extractor_error import ExtractorError
from justin.actions.named.stage.models.stage import stub_stage
from justin.actions.named.stage.models.stages_factory import StagesFactory
from justin.shared.helpers.checks_runner import ChecksRunner
from justin.shared.models.photoset import Photoset


class StageAction(NamedAction):

    def __init__(self, factory: StagesFactory) -> None:
        super().__init__()

        self.__stages_factory = factory

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        # check if able to exit
        # cleanup
        # check if able to enter
        # move
        # prepare

        new_stage = self.__stages_factory.stage_by_command(args.command)
        current_stage = self.__stages_factory.stage_by_path(photoset.path)

        if current_stage is None:
            current_stage = stub_stage

        assert isinstance(photoset, Photoset)

        print(f"Trying to move \"{photoset.name}\" to stage \"{new_stage.name}\"")

        transfer_checks = current_stage.outcoming_checks + new_stage.incoming_checks

        checks_runner = ChecksRunner.instance()

        root = context.world.location_of_path(photoset.path)

        new_stage_folder = root / "stages" / new_stage.folder

        try:
            photoset_parts = photoset.parts

            for photoset_part in photoset_parts:
                current_stage.cleanup(photoset_part)

                for check in transfer_checks:
                    check.rollback(photoset_part)

                print(f"Running checks")

                checks_runner.run(photoset_part, transfer_checks)

            if new_stage != current_stage:
                photoset.move(new_stage_folder)

            for photoset_part in photoset_parts:
                new_stage.prepare(photoset_part)

        except (ExtractorError, CheckFailedError) as error:
            print(f"Unable to {new_stage.name} {photoset.name}: {error}")
        else:
            print("Moved successfully")
