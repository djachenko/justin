from argparse import ArgumentParser

from v3_0.commands.command import Command
from v3_0.models.photoset import Photoset
from v3_0.models.stages.stage import Stage
from v3_0.models.stages.stages_factory import StagesFactory
from v3_0.models.world import World


# todo: introduce f-strings
# todo: mak multi-set mode

class StageCommand(Command):

    def __init__(self, world: World) -> None:
        super().__init__()

        self.__factory = StagesFactory(world)

    def configure_parser(self, parser_adder):
        for command in self.__factory.commands:
            subparser: ArgumentParser = parser_adder.add_parser(command)

            subparser.add_argument("name", nargs="+")
            subparser.set_defaults(new_stage=self.__factory.stage_by_command(command))

            self.setup_callback(subparser)

    def run(self, args) -> None:

        # check if able to exit
        # cleanup
        # check if able to enter
        # move
        # prepare

        world = args.world

        #
        new_stage: Stage = args.new_stage

        for photoset_name in args.name:
            photosets = world[photoset_name]

            photoset = photosets[0]

            current_stage = self.__factory.stage_by_path(photoset.path)

            assert isinstance(photoset, Photoset)

            print("Trying to move \"{photoset} to stage {stage}\"".format(photoset=photoset.name, stage=new_stage.name))

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
                print("Unable to {stage_name} {set_name}. Something happened.".format(
                    stage_name=new_stage.name, set_name=photoset.name))
