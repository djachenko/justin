from argparse import ArgumentParser

from v3_0.commands.command import Command
from v3_0.shared.models.photoset import Photoset
from v3_0.stage.models.stage import Stage
from v3_0.stage.models.stages_factory import StagesFactory


class StageCommand(Command):

    def __init__(self, factory: StagesFactory) -> None:
        super().__init__()

        self.__stages_factory = factory

    def configure_parser(self, parser_adder):
        for stage in self.__stages_factory.stages():
            command = stage.command

            subparser: ArgumentParser = parser_adder.add_parser(command)

            subparser.add_argument("name", nargs="+")
            subparser.set_defaults(new_stage=stage)

            self.setup_callback(subparser)

    def run(self, args) -> None:

        # check if able to exit
        # cleanup
        # check if able to enter
        # move
        # prepare

        world = args.world

        new_stage: Stage = args.new_stage

        for photoset_name in args.name:
            photosets = world[photoset_name]

            photoset = photosets[0]

            current_stage = self.__stages_factory.stage_by_path(photoset.path)

            assert isinstance(photoset, Photoset)

            print(f"Trying to move \"{photoset.name}\" to stage \"{new_stage.name}\"")

            success = False

            if current_stage.able_to_come_out(photoset):
                current_stage.cleanup(photoset)

                if new_stage.able_to_come_in(photoset):
                    if new_stage != current_stage:
                        new_stage.transfer(photoset)

                    new_stage.prepare(photoset)

                    success = True
                else:
                    current_stage.prepare(photoset)

            if success:
                print("Moved successfully")
            else:
                print(f"Unable to {new_stage.name} {photoset.name}. Something happened.")
