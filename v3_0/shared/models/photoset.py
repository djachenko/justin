from pathlib import Path
from typing import List, Iterable, Optional

from v3_0.shared.filesystem.file import File
from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree
from v3_0.shared.filesystem.movable import Movable
from v3_0.shared.helpers import joins
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
    def instagram(self) -> FolderTree:
        return self.tree[Photoset.__INSTAGRAM]

    @property
    def parts(self) -> List['Photoset']:
        parts_folders = PartingHelper.folder_tree_parts(self.tree)
        parts = [Photoset(part_folder) for part_folder in parts_folders]

        return parts

    @property
    def our_people(self) -> FolderTree:
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
        return self.__subtree_files(Photoset.__PHOTOCLUB)

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
    def justin(self) -> FolderTree:
        return self.tree[Photoset.__JUSTIN]

    @property
    def gif(self) -> FolderTree:
        return self.tree[Photoset.__GIF]

    @property
    def closed(self) -> FolderTree:
        return self.tree[Photoset.__CLOSED]

    @property
    def results(self) -> List[File]:
        possible_subtrees = [
            self.instagram,
            self.our_people,
            self.justin,
            self.closed
        ]

        possible_subtrees = [i for i in possible_subtrees if i is not None]

        results_lists = [sub.flatten() for sub in possible_subtrees]

        if self.photoclub is not None:
            results_lists.append(self.photoclub)

        result = []

        for results_list in results_lists:
            result += results_list

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

    def split_bases(self) -> List[Iterable[File]]:
        mandatory_trees = [
            self.justin,
            self.our_people,
            self.closed,
        ]

        optional_trees = [
            self.gif,
            self.instagram,
        ]

        mandatory_bases = [tree.files for tree in mandatory_trees]
        optional_bases = [tree.files for tree in optional_trees if len(tree.subtree_names) > 0]

        all_bases = mandatory_bases + optional_bases

        non_empty_bases = [i for i in all_bases if len(i) > 0]

        return non_empty_bases

    # def split_backwards(self, base: Iterable[File], new_path: AbsolutePath)):

    def split_forward(self, base: Iterable[File], new_path: Path):
        sources = self.sources
        results = self.big_jpegs

        sources_join = joins.inner(
            base,
            sources,
            lambda x, s: x.stem() == s.name
        )

        results_join = joins.inner(
            base,
            results,
            lambda a, b: a.name == b.name
        )

        sources_to_move = [i[1] for i in sources_join]
        results_to_move = [i[1] for i in results_join]

        new_path = new_path / self.name

        for source in sources_to_move:
            source.move(new_path)

        # for result in results_to_move:
        #     result_relative_path: RelativePath = result.path - self.path
        #     result_absolute_path = new_path + result_relative_path
        #
        #     result_folder_absolute_path = result_absolute_path.parent()
        #
        #     result.move(result_folder_absolute_path)
