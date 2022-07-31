from typing import List, Optional

from justin_utils import util

from justin.shared.filesystem import FolderTree, File, TreeBased
from justin.shared.helpers.parts import PartsMixin
from justin.shared.models import sources
from justin.shared.models.sources import Source


class Photoset(TreeBased, PartsMixin):
    __GIF = "gif"
    __CLOSED = "closed"
    __JUSTIN = "justin"
    __MEETING = "meeting"
    __KOT_I_KIT = "kot_i_kit"
    __SELECTION = "not_signed"
    __PHOTOCLUB = "photoclub"
    __OUR_PEOPLE = "my_people"

    def __init__(self, tree: FolderTree) -> None:
        super().__init__(tree)

        from justin.shared.models.photoset_migration import ALL_MIGRATIONS

        for migration in ALL_MIGRATIONS:
            migration.migrate(self)

    def __str__(self) -> str:
        return "Photoset: " + self.tree.name

    @property
    def parts(self) -> List['Photoset']:
        if not self.is_parted:
            return [self]

        parts = [Photoset(part_folder) for part_folder in super().parts]

        return parts

    @property
    def our_people(self) -> Optional[FolderTree]:
        return self.tree[Photoset.__OUR_PEOPLE]

    @property
    def sources(self) -> List[Source]:
        sources_ = sources.parse_sources(self.tree.files)

        return sources_

    def __subtree_files(self, key: str) -> Optional[List[File]]:
        subtree = self.tree[key]

        if subtree is not None:
            return subtree.files
        else:
            return None

    @property
    def photoclub(self) -> Optional[FolderTree]:
        return self.tree[Photoset.__PHOTOCLUB]

    @property
    def selection(self) -> Optional[List[File]]:
        result = self.__subtree_files(Photoset.__SELECTION)

        if result is None:
            return []

        return result

    @property
    def justin(self) -> Optional[FolderTree]:
        return self.tree[Photoset.__JUSTIN]

    @property
    def gif(self) -> FolderTree:
        return self.tree[Photoset.__GIF]

    @property
    def closed(self) -> Optional[FolderTree]:
        return self.tree[Photoset.__CLOSED]

    @property
    def meeting(self) -> Optional[FolderTree]:
        return self.tree[Photoset.__MEETING]

    @property
    def kot_i_kit(self) -> Optional[FolderTree]:
        return self.tree[Photoset.__KOT_I_KIT]

    @property
    def results(self) -> List[File]:
        possible_subtrees = [
            self.our_people,
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

        if self.selection is not None:
            jpegs += self.selection

        return jpegs
