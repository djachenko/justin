from pathlib import Path
from typing import List

from justin.shared.filesystem import Folder, File, FolderBased
from justin.shared.helpers.parts import PartsMixin
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
    def parts(self) -> List['Photoset']:
        if not self.is_parted:
            return [self]

        parts = [Photoset.from_tree(part_folder) for part_folder in super().parts]

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
    def photoclub(self) -> Folder | None:
        return self.folder[Photoset.__PHOTOCLUB]

    @property
    def not_signed(self) -> List[File] | None:
        result = self.__subtree_files(Photoset.__NOT_SIGNED)

        if result is None:
            return []

        return result

    @property
    def justin(self) -> Folder | None:
        return self.folder[Photoset.__JUSTIN]

    @property
    def gif(self) -> Folder | None:
        return self.folder[Photoset.__GIF]

    @property
    def timelapse(self) -> Folder | None:
        return self.folder["timelapse"]

    @property
    def closed(self) -> Folder | None:
        return self.folder[Photoset.__CLOSED]

    @property
    def meeting(self) -> Folder | None:
        return self.folder[Photoset.__MEETING]

    @property
    def kot_i_kit(self) -> Folder | None:
        return self.folder[Photoset.__KOT_I_KIT]

    @property
    def my_people(self) -> Folder | None:
        return self.folder[Photoset.__MY_PEOPLE]

    @property
    def results(self) -> List[File]:
        possible_subtrees = [
            self.my_people,
            self.justin,
            self.closed,
            self.photoclub,
            self.meeting,
            self.kot_i_kit,
        ]

        possible_subtrees = [i for i in possible_subtrees if i is not None]

        results_lists = [sub.flatten() for sub in possible_subtrees]

        result = util.flatten(results_lists)

        return result

    @property
    def big_jpegs(self) -> List[File]:
        jpegs = self.results

        if self.not_signed is not None:
            jpegs += self.not_signed

        return jpegs

    @classmethod
    def from_tree(cls, tree: Folder) -> 'Photoset':
        photoset = Photoset(tree)

        from justin.shared.models.photoset_migration import ALL_MIGRATIONS

        for migration in ALL_MIGRATIONS:
            migration.migrate(photoset)

        return photoset

    @classmethod
    def from_path(cls, path: Path) -> 'Photoset':
        return Photoset.from_tree(Folder(path))
