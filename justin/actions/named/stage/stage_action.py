from argparse import Namespace

from justin.actions.pattern_action import Extra
from justin.actions.named.stage.models.stages_factory import StagesFactory
from justin.actions.pattern_action import PatternAction
from justin.shared.context import Context
from justin.shared.helpers.checks_runner import ChecksRunner
from justin.shared.models.photoset import Photoset


class StageAction(PatternAction):

    def __init__(self, factory: StagesFactory) -> None:
        super().__init__()

        self.__stages_factory = factory
        self.__checks_runner = ChecksRunner.instance()

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        # check if able to exit
        # cleanup
        # check if able to enter
        # move
        # prepare

        new_stage = self.__stages_factory.stage_by_command(args.command_name)
        current_stage = self.__stages_factory.stage_by_path(photoset.path) or self.__stages_factory.stub()

        assert isinstance(photoset, Photoset)

        print(f"Trying to move \"{photoset.name}\" to stage \"{new_stage.name}\"")

        transfer_checks = current_stage.outcoming_checks + new_stage.incoming_checks

        root = context.world.location_of_path(photoset.path)

        photoset_parts = photoset.parts

        problems = []

        for photoset_part in photoset_parts:
            problems += current_stage.cleanup(photoset_part)

            if problems:
                break

            for check in transfer_checks:
                problems += check.rollback(photoset_part)

                if problems:
                    break

            if problems:
                break

            print(f"Running checks")

            problems += self.__checks_runner.run(photoset_part, transfer_checks)

        if problems:
            print(f"Unable to {new_stage.name} {photoset.name}:")

            for problem in problems:
                print(problem)
        else:
            if new_stage != current_stage:
                # todo: new_stage.accept(photoset)
                # photoset.move(new_stage_folder)

                new_stage.transfer(photoset, root)

            for photoset_part in photoset_parts:
                new_stage.prepare(photoset_part)

            print("Moved successfully")
