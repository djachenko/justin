from typing import List

from filesystem.file import File
from filesystem.folder import Folder
from filesystem.folder_based import FileBased
from models.folder_tree import FolderTree, SingleFolderTree
from models.source import Source


class Photoset(FileBased):
    __GIF = "gif"
    __CLOSED = "closed"
    __JUSTIN = "justin"
    __SELECTION = "selection"
    __PHOTOCLUB = "photoclub"
    __OUR_PEOPLE = "our_people"
    __INSTAGRAM = "instagram"
    __EDITED_SOURCES = "edited_sources"

    def __init__(self, entry: Folder, destination="", category=""):
        super().__init__(entry)

        self.destination = destination
        self.category = category

    @property
    def tree(self) -> FolderTree:
        return SingleFolderTree(self.entry)

    def __str__(self) -> str:
        return "Photoset: " + self.path.to_string()

    @property
    def edited_sources(self) -> List[Source]:
        return Source.from_file_sequence(self.tree[Photoset.__EDITED_SOURCES].files)

    @property
    def edited_sources_folder_name(self):
        return Photoset.__EDITED_SOURCES

    @property
    def instagram(self) -> FolderTree:
        return self.tree[Photoset.__INSTAGRAM]

    @property
    def parts(self) -> List['Photoset']:
        parts_folders = [subfolder for subfolder in self.entry.subfolders() if subfolder.name.split(".")[0].isdecimal()]
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

    @property
    def photoclub(self) -> List[File]:
        return self.tree[Photoset.__PHOTOCLUB].files

    @property
    def selection(self) -> List[File]:
        return self.tree[Photoset.__SELECTION].files

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
        return self.photoclub + self.instagram.flatten() + self.our_people.flatten() + self.justin.flatten() + \
               self.closed.flatten()
