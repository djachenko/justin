from argparse import ArgumentParser

from command.command import Command
from justin import Args
from v3_0.models.path_interpretation import PathInterpretation
from v3_0.models.photoset import Photoset
from v3_0.models.stages import stage
from v3_0.models.stages.stage import Stage


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

    @staticmethod
    def __handle_photoset(photoset: Photoset, new_stage: Stage):

        photoset_path = photoset.path
        path_interpretation = PathInterpretation.interpret(photoset_path)

        if path_interpretation.destination != "stages":
            print("Photoset {photoset_name} is not staged".format(photoset_name=photoset.name))

            return

        current_stage_name = path_interpretation.category

        current_stage = StageCommand2.stages_by_folder[current_stage_name]

        print("Trying to move photoset {photoset} to stage {stage}".format(
            photoset=photoset.name,
            stage=new_stage.name
        ))

        if not current_stage.able_to_come_out(photoset):
            print(f"Unable to move {photoset.name} from {current_stage.name}")

            return

        current_stage.cleanup(photoset)

        if not new_stage.able_to_come_in(photoset):
            print(f"Unable to move {photoset.name} to {new_stage.name}")

            current_stage.prepare(photoset)

            return

        if new_stage != current_stage:
            new_stage.transfer(photoset)

        new_stage.prepare(photoset)

        print(f"{photoset.name} moved successfully")

    def run(self, args: Args) -> None:
        world = args.world
        new_stage: Stage = args.new_stage

        for photoset_name in args.name:
            photoset = world[photoset_name]

            if photoset is None:
                print("There is no photoset with name \"{name}\"".format(name=photoset_name))
                continue

            self.__handle_photoset(photoset, new_stage)
