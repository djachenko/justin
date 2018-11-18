from argparse import ArgumentParser

from command.command import Command
from v3_0.models.stages import stage
from v3_0.models.photoset import Photoset
from v3_0.models.stages.stage import Stage


class StageCommand(Command):
    stages = stage.ALL_STAGES

    stages_by_command = {stage_.command: stage_ for stage_ in stages}
    stages_by_folder = {stage_.folder: stage_ for stage_ in stages}

    def configure_parser(self, parser_adder):
        command_keys = StageCommand.stages_by_command.keys()

        for command in command_keys:
            subparser: ArgumentParser = parser_adder.add_parser(command)

            subparser.add_argument("name", nargs="+")
            subparser.set_defaults(new_stage=StageCommand.stages_by_command[command])

            self.setup_callback(subparser)

    def run(self, args) -> None:

        # check if able to exit
        # cleanup
        # check if able to enter
        # move
        # prepare

        world = args.world

        current_stage: Stage = StageCommand.stages_by_folder[args.path.parts[-1]]
        new_stage: Stage = args.new_stage

        enclosing_disk = world.disk_by_path(args.path)

        for photoset_name in args.name:
            photoset_path = args.path.append_component(photoset_name)

            if not world.valid_path(photoset_path):
                print("Path \"{path}\" is not valid path".format(path=photoset_path))

                continue

            photoset = world.element_by_path(photoset_path)

            assert isinstance(photoset, Photoset)

            print("Trying to move \"{photoset} to stage {stage}\"".format(photoset=photoset.name, stage=new_stage.name))

            if current_stage.able_to_come_out(photoset):
                current_stage.cleanup(photoset)

                if new_stage.able_to_come_in(photoset):
                    if new_stage != current_stage:
                        new_stage.transfer(photoset, enclosing_disk)

                    new_stage.prepare(photoset)

                    print("Moved successfully")

                    continue
                else:
                    current_stage.prepare(photoset)

            print("Unable to {stage_name} {set_name}. Something happened.".format(
                stage_name=new_stage.name, set_name=photoset.name))
