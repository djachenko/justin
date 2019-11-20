from argparse import Namespace

from pyvko.models.group import Group

from v3_0.actions.action import Action
from v3_0.actions.checks_runner import ChecksRunner
from v3_0.actions.stage.exceptions.check_failed_error import CheckFailedError
from v3_0.actions.stage.logic.exceptions.extractor_error import ExtractorError
from v3_0.actions.stage.models.stages_factory import StagesFactory
from v3_0.shared.filesystem.folder_tree.single_folder_tree import SingleFolderTree
from v3_0.shared.helpers import util
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class StageAction(Action):
    def __init__(self, factory: StagesFactory) -> None:
        super().__init__()

        self.__stages_factory = factory

    def perform(self, args: Namespace, world: World, group: Group) -> None:

        # check if able to exit
        # cleanup
        # check if able to enter
        # move
        # prepare

        new_stage = self.__stages_factory.stage_by_command(args.command)

        for path in util.resolve_patterns(args.name):
            photoset = Photoset(SingleFolderTree(path))

            current_stage = self.__stages_factory.stage_by_path(photoset.path)

            assert isinstance(photoset, Photoset)

            print(f"Trying to move \"{photoset.name}\" to stage \"{new_stage.name}\"")

            transfer_checks = current_stage.outcoming_checks + new_stage.incoming_checks

            try:
                current_stage.cleanup(photoset)

                for check in transfer_checks:
                    check.rollback(photoset)

                checks_runner = ChecksRunner.instance()

                print("Running checks")

                checks_runner.run(photoset, transfer_checks)

                if new_stage != current_stage:
                    new_stage.transfer(photoset)

                new_stage.prepare(photoset)
            except (ExtractorError, CheckFailedError) as error:
                print(f"Unable to {new_stage.name} {photoset.name}: {error}")
            else:
                print("Moved successfully")
