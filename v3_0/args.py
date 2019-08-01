import argparse
from functools import lru_cache

from pyvko.group.group import Group
from pyvko.photos.photos_uploader import PhotosUploader

from v3_0.shared.models.world import World


class Args(argparse.Namespace):
    @staticmethod
    @lru_cache()
    def instance() -> 'Args':
        # pyvko = Pyvko()

        return Args(World.instance())

    def __init__(self, world: World, group: Group = None, uploader: PhotosUploader = None) -> None:
        super().__init__()

        self.__world = world
        self.__group = group
        self.__uploader = uploader

    @property
    def world(self) -> World:
        return self.__world

    @property
    def group(self) -> Group:
        return self.__group

    @property
    def uploader(self) -> PhotosUploader:
        return self.__uploader
