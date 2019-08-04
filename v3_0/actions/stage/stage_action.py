from argparse import Namespace

from pyvko.group.group import Group
from pyvko.photos.photos_uploader import PhotosUploader

from v3_0.actions.action import Action
from v3_0.actions.stage.models.stage import Stage
from v3_0.actions.stage.models.stages_factory import StagesFactory
from v3_0.shared.models.photoset import Photoset
from v3_0.shared.models.world import World


class StageAction(Action):
    def __init__(self, factory: StagesFactory) -> None:
        super().__init__()

        self.__stages_factory = factory

    def perform(self, args: Namespace, world: World, group: Group, uploader: PhotosUploader) -> None:

        # check if able to exit
        # cleanup
        # check if able to enter
        # move
        # prepare

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
