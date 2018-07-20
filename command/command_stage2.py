from argparse import ArgumentParser

from command.command import Command
from models import stage
from models.photoset import Photoset
from models.stage import Stage
from models2.world2 import World2


class StageCommand2(Command):
    stages = stage.ALL_STAGES

    stages_by_command = {stage_.command: stage_ for stage_ in stages}
    stages_by_folder = {stage_.folder: stage_ for stage_ in stages}

    def configure_parser(self, parser_adder):
        command_keys = StageCommand2.stages_by_command.keys()

        for command in command_keys:
            subparser: ArgumentParser = parser_adder.add_parser(command)

            subparser.add_argument("name", nargs="+")
            subparser.set_defaults(new_stage=StageCommand2.stages_by_command[command])

            self.setup_callback(subparser)

    def handle_photoset(self, name: str, args):
        world = World2()

        new_stage: Stage = args.new_stage

        photoset_path = args.path.append_component(name)

        photoset = world[name]

        if photoset is None:
            print("There is no photoset with name \"{name}\"".format(name=photoset_name))

            return

        if photoset.destination != "stages":
            print("Photoset {photoset_name} is not staged".format(photoset_name=photoset.name))

            return

        current_stage_name = photoset.category

        current_stage = StageCommand2.stages_by_folder[current_stage_name]

        print("Trying to move photoset {photoset} to stage {stage}".format(photoset=photoset.name, stage=new_stage.name))

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

    def run(self, args) -> None:

        # check if able to exit
        # cleanup
        # check if able to enter
        # move
        # prepare

        world = World2()

        new_stage: Stage = args.new_stage

        enclosing_disk = world.disk_by_path(args.path)

        for photoset_name in args.name:
            photoset_path = args.path.append_component(photoset_name)

            photoset = world[photoset_name]

            if photoset is None:
                print("There is no photoset with name \"{name}\"".format(name=photoset_name))
                continue

            if photoset.destination != "stages":
                print("Photoset {photoset_name} is not staged".format(photoset_name=photoset.name))



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
