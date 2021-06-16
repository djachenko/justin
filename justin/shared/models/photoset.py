from abc import abstractmethod, ABC
from pathlib import Path
from typing import List, Optional

from justin_utils import util
from justin_utils.multiplexer import Multiplexable

from justin.shared.filesystem import FolderTree, File, TreeBased
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import PhotosetMetafile
from justin.shared.models import sources
from justin.shared.models.sources import Source


class Metafiled(ABC):
    @property
    @abstractmethod
    def metafile_path(self) -> Path:
        pass

    def has_metafile(self) -> bool:
        return self.metafile_path.exists()

    def get_metafile(self) -> PhotosetMetafile:
        return PhotosetMetafile.read(self.metafile_path)

    def save_metafile(self, metafile: PhotosetMetafile):
        metafile.write(self.metafile_path)


class Photoset(TreeBased, Multiplexable, Metafiled):
    __GIF = "gif"
    __CLOSED = "closed"
    __JUSTIN = "justin"
    __SELECTION = "selection"
    __PHOTOCLUB = "photoclub"
    __OUR_PEOPLE = "our_people"
    __INSTAGRAM = "instagram"

    __METAFILE = "_meta.json"

    @property
    def metafile_path(self) -> Path:
        return self.tree.path / Photoset.__METAFILE

    def stem(self) -> str:
        assert False

        # noinspection PyUnreachableCode
        return self.name

    def __str__(self) -> str:
        return "Photoset: " + self.tree.name

    @property
    def instagram(self) -> Optional[FolderTree]:
        return self.tree[Photoset.__INSTAGRAM]

    @property
    def parts(self) -> List['Photoset']:
        parts_folders = folder_tree_parts(self.tree)
        parts = [Photoset(part_folder) for part_folder in parts_folders]

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
    def photoclub(self) -> Optional[List[File]]:
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
    def results(self) -> List[File]:
        possible_subtrees = [
            self.instagram,
            self.our_people,
            self.justin,
            self.closed,
            self.photoclub,
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
