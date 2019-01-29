from pathlib import Path
from typing import List, Iterable

from v3_0.filesystem.file import File
from v3_0.filesystem.folder_tree.folder_tree import FolderTree
from v3_0.filesystem.movable import Movable
from v3_0.helpers import joins
from v3_0.models.source import Source


class Photoset(Movable):
    __GIF = "gif"
    __CLOSED = "closed"
    __JUSTIN = "justin"
    __SELECTION = "selection"
    __PHOTOCLUB = "photoclub"
    __OUR_PEOPLE = "our_people"
    __INSTAGRAM = "instagram"
    __EDITED_SOURCES = "edited_sources"

    def __init__(self, entry: FolderTree):
        self.__tree = entry

    @property
    def tree(self) -> FolderTree:
        return self.__tree

    @property
    def path(self) -> Path:
        return self.tree.path

    @property
    def name(self) -> str:
        return self.tree.name

    def __str__(self) -> str:
        return "Photoset: " + self.tree.name

    @property
    def edited_sources(self) -> List[Source]:
        return Source.from_file_sequence(self.__subtree_files(Photoset.__EDITED_SOURCES))

    @property
    def edited_sources_folder_name(self):
        return Photoset.__EDITED_SOURCES

    @property
    def instagram(self) -> FolderTree:
        return self.tree[Photoset.__INSTAGRAM]

    @property
    def parts(self) -> List['Photoset']:
        parts_names = [name for name in self.tree.subtree_names if name.split(".")[0].isdecimal()]
        parts_folders = [self.tree[name] for name in parts_names]
        parts = [Photoset(part_folder) for part_folder in parts_folders]

        return parts

    @property
    def our_people(self) -> FolderTree:
        return self.tree[Photoset.__OUR_PEOPLE]

    @property
    def sources(self) -> List[Source]:
        return Source.from_file_sequence(self.tree.files) + \
               self.edited_sources

    @property
    def sources_folder_name(self):
        return ""

    def __subtree_files(self, key: str) -> List[File]:
        subtree = self.tree[key]

        if subtree is not None:
            return subtree.files
        else:
            return []

    @property
    def photoclub(self) -> List[File]:
        return self.__subtree_files(Photoset.__PHOTOCLUB)

    @property
    def selection(self) -> List[File]:
        return self.__subtree_files(Photoset.__SELECTION)

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

        results_lists = [self.photoclub] + [sub.flatten() for sub in possible_subtrees]

        result = []

        for results_list in results_lists:
            result += results_list

        return result

    @property
    def big_jpegs(self) -> List[File]:
        return self.results + self.selection

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
            lambda x, s: x.name_without_extension() == s.name
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
