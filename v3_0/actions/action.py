from abc import abstractmethod
from argparse import Namespace

from pyvko.group.group import Group
from pyvko.photos.photos_uploader import PhotosUploader

from v3_0.shared.models.world import World


class Action:
    @abstractmethod
    def perform(self, args: Namespace, world: World, group: Group, uploader: PhotosUploader) -> None:
        pass
