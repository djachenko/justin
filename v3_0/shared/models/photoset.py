from pathlib import Path
from typing import List, Optional

from v3_0.shared.filesystem.file import File
from v3_0.shared.filesystem.folder_tree import FolderTree
from v3_0.shared.filesystem.movable import Movable
from v3_0.shared.helpers import util
from v3_0.shared.helpers.parting_helper import PartingHelper
from v3_0.shared.metafiles.photoset_metafile import PhotosetMetafile
from v3_0.shared.models.source.source import Source
from v3_0.shared.models.source.sources_parser import SourcesParser


class Photoset(Movable):
    __GIF = "gif"
    __CLOSED = "closed"
    __JUSTIN = "justin"
    __SELECTION = "selection"
    __PHOTOCLUB = "photoclub"
    __OUR_PEOPLE = "our_people"
    __INSTAGRAM = "instagram"

    __METAFILE = "_meta.json"

    def __init__(self, entry: FolderTree):
        self.__tree = entry

    @property
    def tree(self) -> FolderTree:
        return self.__tree

    @property
    def __metafile_path(self) -> Path:
        return self.tree.path / Photoset.__METAFILE

    def has_metafile(self) -> bool:
        return self.__metafile_path.exists()

    def get_metafile(self) -> PhotosetMetafile:
        return PhotosetMetafile.read(self.__metafile_path)

    def save_metafile(self, metafile: PhotosetMetafile):
        metafile.write(self.__metafile_path)

    @property
    def path(self) -> Path:
        return self.tree.path

    @property
    def name(self) -> str:
        return self.tree.name

    def stem(self) -> str:
        return self.name

    def __str__(self) -> str:
        return "Photoset: " + self.tree.name

    @property
    def instagram(self) -> Optional[FolderTree]:
        return self.tree[Photoset.__INSTAGRAM]

    @property
    def parts(self) -> List['Photoset']:
        parts_folders = PartingHelper.folder_tree_parts(self.tree)
        parts = [Photoset(part_folder) for part_folder in parts_folders]

        return parts

    @property
    def our_people(self) -> Optional[FolderTree]:
        return self.tree[Photoset.__OUR_PEOPLE]

    @property
    def sources(self) -> List[Source]:
        sources = SourcesParser.from_file_sequence(self.tree.files)

        return sources

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
    def selection_folder_name(self) -> str:
        return Photoset.__SELECTION

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

    @property
    def all_jpegs(self) -> List[File]:
        return self.big_jpegs + self.gif.flatten()

    def move(self, path: Path):
        self.tree.move(path)

    def move_down(self, subfolder: str) -> None:
        self.tree.move_down(subfolder)

    def move_up(self) -> None:
        self.tree.move_up()

    def copy(self, path: Path) -> None:
        self.tree.copy(path)
