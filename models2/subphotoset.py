from typing import List, Iterable

import util
from filesystem2.absolute_path import AbsolutePath
from filesystem2.file import File
from filesystem2.folder import Folder
from filesystem2.folder_based import FileBased
from filesystem2.path import Path
from filesystem2.relative_path import RelativePath
from models.folder_tree import FolderTree, SingleFolderTree
from models2.source import Source


class SubPhotoset(FileBased):
    __GIF = "gif"
    __CLOSED = "closed"
    __JUSTIN = "justin"
    __SELECTION = "selection"
    __PHOTOCLUB = "photoclub"
    __OUR_PEOPLE = "our_people"
    __INSTAGRAM = "instagram"
    __EDITED_SOURCES = "edited_sources"

    def __init__(self, entry: Folder):
        super().__init__(entry)

    @property
    def tree(self) -> FolderTree:
        return SingleFolderTree(self.entry)

    def __str__(self) -> str:
        return "Photoset: " + self.path.to_string()

    @property
    def edited_sources(self) -> List[Source]:
        return Source.from_file_sequence(self.tree[SubPhotoset.__EDITED_SOURCES].files)

    @property
    def edited_sources_folder_name(self):
        return SubPhotoset.__EDITED_SOURCES

    @property
    def instagram(self) -> FolderTree:
        return self.tree[SubPhotoset.__INSTAGRAM]

    @property
    def parts(self) -> List['SubPhotoset']:
        parts_folders = [subfolder for subfolder in self.entry.subfolders() if subfolder.name.split_forward(".")[0].isdecimal()]
        parts = [SubPhotoset(part_folder) for part_folder in parts_folders]

        return parts

    @property
    def our_people(self) -> FolderTree:
        return self.tree[SubPhotoset.__OUR_PEOPLE]

    @property
    def sources(self) -> List[Source]:
        return Source.from_file_sequence(self.tree.files) + \
               self.edited_sources

    @property
    def sources_folder_name(self):
        return ""

    @property
    def photoclub(self) -> List[File]:
        return self.tree[SubPhotoset.__PHOTOCLUB].files

    @property
    def selection(self) -> List[File]:
        return self.tree[SubPhotoset.__SELECTION].files

    @property
    def selection_folder_name(self) -> str:
        return SubPhotoset.__SELECTION

    @property
    def justin(self) -> FolderTree:
        return self.tree[SubPhotoset.__JUSTIN]

    @property
    def gif(self) -> FolderTree:
        return self.tree[SubPhotoset.__GIF]

    @property
    def closed(self) -> FolderTree:
        return self.tree[SubPhotoset.__CLOSED]

    @property
    def results(self) -> List[File]:
        return self.photoclub + \
               self.instagram.flatten() + \
               self.our_people.flatten() + \
               self.justin.flatten() + \
               self.closed.flatten()

    @property
    def big_jpegs(self) -> List[File]:
        return self.results + self.selection

    @property
    def all_jpegs(self) -> List[File]:
        return self.big_jpegs + self.gif.flatten()

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

    def split_backwards(self, base: Iterable[File], new_path: AbsolutePath)):

    def split_forward(self, base: Iterable[File], new_path: AbsolutePath):
        sources = self.sources
        results = self.big_jpegs

        sources_join = util.inner_join(
            base,
            sources,
            lambda x: x.name_without_extension(),
            lambda s: s.name
        )

        results_join = util.inner_join(
            base,
            results,
            lambda x: x.name
        )

        sources_to_move = [i[1] for i in sources_join]
        results_to_move = [i[1] for i in results_join]

        new_path = new_path.append_component(self.name)

        for source in sources_to_move:
            source.move(new_path)

        for result in results_to_move:
            result_relative_path: RelativePath = result.path - self.path
            result_absolute_path = new_path + result_relative_path

            result_folder_absolute_path = result_absolute_path.parent()

            result.move(result_folder_absolute_path)

            a = 7
