from typing import List, Iterable

from collect_trace import CollectTrace
from filesystem.folder import Folder
from filesystem.folder_based import FileBased
from filesystem.path import Path
from models.photoset import Photoset


class Category(FileBased):
    def __init__(self, entry: Folder) -> None:
        super().__init__(entry)

    @property
    def sets(self) -> List[Photoset]:
        subfolders = self.entry.subfolders()

        return list(map(Photoset, subfolders))

    def __getitem__(self, key) -> Photoset:
        return next(i for i in self.sets if i.name == key)

    def __iter__(self):
        return iter(self.sets)

    def element_by_path(self, path: Path) -> object:
        assert self.path.is_subpath(path)

        return next(filter(lambda file: file.path == path, self.sets), None)

    def collect(self, trace: CollectTrace) -> Iterable[Photoset]:
        pass
