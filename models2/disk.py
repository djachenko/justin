from typing import Iterable, Optional

import structure
from filesystem2.absolute_path import AbsolutePath
from filesystem2.filesystem import Filesystem
from models2.subphotoset import SubPhotoset
from structure import Structure


class Disk:
    def __init__(self, root_path: AbsolutePath) -> None:
        super().__init__()

        self.root_path = root_path

    @property
    def sets(self) -> Iterable[SubPhotoset]:
        shared_structure = structure.disk_structure

        result = Disk.__collect(self.root_path, shared_structure)

        return result

    def __getitem__(self, key: str) -> Optional[SubPhotoset]:
        for photoset in self.sets:
            if photoset.name == key:
                return photoset

        return None

    def collide(self):
        sets = self.sets

        mapping = {}

        for photoset in sets:
            key = photoset.name
            bucket = mapping.get(key, [])

            bucket.append(photoset)

            mapping[key] = bucket

        buckets = mapping.values()

        collisions = [bucket for bucket in buckets if len(bucket) > 1]

    @staticmethod
    def __collect(trace: AbsolutePath, root: Structure) -> Iterable[SubPhotoset]:
        result = []

        for i in root.substructures:
            result += Disk.__collect(trace.append_component(i.name), i)

        if root.has_implicit_sets:
            if len(trace.parts) < 3:
                trace = trace.append_component("")

            path = trace

            if path.exists():
                folder = Filesystem.folder(path)

                subfolders = folder.subfolders()

                photosets = [SubPhotoset(subfolder) for subfolder in subfolders]

                result += photosets

        return result
