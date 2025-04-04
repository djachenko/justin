from pathlib import Path
from typing import List, Self
from uuid import UUID

from justin.shared.filesystem import File, FolderBased
from justin.shared.helpers.parts import PartsMixin
from justin.shared.metafile import PhotosetMetafile, MetaFolder
from justin.shared.models import sources
from justin.shared.models.sources import Source
from justin_utils import util


class Photoset(FolderBased, PartsMixin):
    __GIF = "gif"
    __CLOSED = "closed"
    __JUSTIN = "justin"
    __MEETING = "meeting"
    __KOT_I_KIT = "kot_i_kit"
    __NOT_SIGNED = "not_signed"
    __PHOTOCLUB = "photoclub"
    __MY_PEOPLE = "my_people"

    def __str__(self) -> str:
        return "Photoset: " + self.folder.name

    @property
    def __metafile(self):
        return self.folder.get_metafile(PhotosetMetafile)

    @property
    def folder(self) -> MetaFolder:
        # noinspection PyTypeChecker
        return super().folder

    @property
    def id(self) -> UUID:
        return self.__metafile.photoset_id

    @property
    def parts(self) -> List['Photoset']:
        if not self.is_parted:
            return [self]

        # noinspection PyTypeChecker
        parts = [Photoset.from_folder(part_folder, without_migration=True) for part_folder in super().parts]

        return parts

    @property
    def sources(self) -> List[Source]:
        sources_ = sources.parse_sources(self.folder.files)

        return sources_

    def __subtree_files(self, key: str) -> List[File] | None:
        subtree = self.folder[key]

        if subtree is not None:
            return subtree.files
        else:
            return None

    @property
    def photoclub(self) -> MetaFolder | None:
        return self.folder[Photoset.__PHOTOCLUB]

    @property
    def not_signed(self) -> List[File] | None:
        result = self.__subtree_files(Photoset.__NOT_SIGNED)

        if result is None:
            return []

        return result

    @property
    def justin(self) -> MetaFolder | None:
        return self.folder[Photoset.__JUSTIN]

    @property
    def gif(self) -> MetaFolder | None:
        return self.folder[Photoset.__GIF]

    @property
    def timelapse(self) -> MetaFolder | None:
        return self.folder["timelapse"]

    @property
    def closed(self) -> MetaFolder | None:
        return self.folder[Photoset.__CLOSED]

    @property
    def meeting(self) -> MetaFolder | None:
        return self.folder[Photoset.__MEETING]

    @property
    def kot_i_kit(self) -> MetaFolder | None:
        return self.folder[Photoset.__KOT_I_KIT]

    @property
    def my_people(self) -> MetaFolder | None:
        return self.folder[Photoset.__MY_PEOPLE]

    @property
    def drive(self) -> MetaFolder | None:
        return self.folder["drive"]

    @property
    def results(self) -> List[File]:
        possible_subtrees = [
            self.my_people,
            self.justin,
            self.closed,
            self.photoclub,
            self.meeting,
            self.kot_i_kit,
            self.drive,
        ]

        possible_subtrees = [i for i in possible_subtrees if i is not None]

        results_lists = [sub.flatten() for sub in possible_subtrees]

        result = util.flat_map(results_lists)

        return result

    @property
    def big_jpegs(self) -> List[File]:
        jpegs = self.results

        if self.not_signed is not None:
            jpegs += self.not_signed

        return jpegs

    @staticmethod
    def is_photoset(folder: Path | MetaFolder) -> bool:
        if isinstance(folder, Path):
            return Photoset.is_photoset(MetaFolder.from_path(folder))

        if folder.has_metafile(PhotosetMetafile):
            return True

        name_split = folder.name.split(".")

        if len(name_split) != 4:
            return False

        if not all(i.isdecimal() for i in name_split[:3]):
            return False

        return True

    @classmethod
    def from_folder(cls, folder: MetaFolder, without_migration: bool = False) -> Self | None:
        if not without_migration and not Photoset.is_photoset(folder.path):
            return None

        photoset = Photoset(folder)

        return photoset

    @classmethod
    def from_path(cls, path: Path) -> Self | None:
        return Photoset.from_folder(MetaFolder.from_path(path))
