from typing import List, Iterable

import structure
import util
from collect_trace import CollectTrace
from filesystem.folder import Folder
from filesystem.folder_based import FileBased
from filesystem.path import Path
from models.category import Category
from models.photoset import Photoset


class Destination(FileBased):
    def __init__(self, entry: Folder) -> None:
        super().__init__(entry)

    @property
    def __structure(self):
        return structure.disk_structure[self.name]

    @property
    def has_implicit_sets(self) -> bool:
        return self.__structure.has_implicit_sets

    @property
    def categories(self) -> List[Category]:
        subfolders = self.entry.subfolders()

        potential_categories = filter(lambda x: self.__structure.has_substructure(x.name), subfolders)

        categories = list(map(Category, potential_categories))

        return categories

    @property
    def sets(self) -> List[Photoset]:
        if not self.has_implicit_sets:
            return []

        subfolders = self.entry.subfolders()

        potential_sets = filter(lambda x: self.__structure.has_set(x.name), subfolders)

        sets = list(map(Photoset, potential_sets))

        return sets

    def __str__(self) -> str:
        return "Destination: " + self.name

    def element_by_path(self, path: Path) -> object:
        assert self.path.is_subpath(path)

        category = next(filter(lambda file: file.path.is_subpath(path), self.categories), None)

        if category is not None:
            return category.element_by_path(path)
        else:
            return next(filter(lambda file: file.path == path, self.sets), None)

    def collect(self, trace: CollectTrace) -> Iterable[Photoset]:
        pass
