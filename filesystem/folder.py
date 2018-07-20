from typing import List, Iterable, Optional, Union

import os

from filesystem import fs
from filesystem.file import File
from filesystem.mock_dir_entry import MockDirEntry
from filesystem.path import Path


class Folder(File):
    def __init__(self, entry: Union[os.DirEntry, MockDirEntry]) -> None:
        assert entry.is_dir()

        super().__init__(entry)

    def __subentries(self) -> List[os.DirEntry]:
        return fs.scandir__(self.path.to_string())

    def __items(self) -> List[File]:
        return [File(i) for i in fs.scandir__(self.path.to_string())]

    def subfiles(self) -> List[File]:
        return [File(item) for item in self.__subentries() if item.is_file()]

    def subfolders(self) -> List['Folder']:
        return [Folder(item) for item in self.__subentries() if item.is_dir()]

    def subfolder(self, name: str) -> 'Folder':
        return next(filter(lambda x: x.name == name, self.subfolders()))

    def has_subfolder(self, subfolder_name: str) -> bool:
        return self.path.append_component(subfolder_name).exists()

    def all_files(self) -> List[File]:
        res = self.subfiles()

        for subfolder in self.subfolders():
            res += subfolder.all_files()

        return res

    def files_by_extensions(self, *extensions: str) -> Iterable[File]:
        extensions = [extension.lower() for extension in extensions]

        return list(filter(lambda file: file.extension in extensions, self.subfiles()))

    # def remove(self):
    #     fs.remove_tree(self.path.to_string())

    def get_item_by_path(self, path: Path) -> Optional[File]:
        assert self.path.is_subpath(path)

        if self.path.depth == path.depth + 1:
            return next(filter(lambda file: file.path == path, self.subfiles()), None)
        else:
            return next(filter(lambda folder: folder.path.is_subpath(path), self.subfolders()), None)

    def __str__(self) -> str:
        return "Folder ({path})".format(path=self.path)

    @classmethod
    def from_file(cls, file: File):
        assert file.is_dir()

        return Folder(file.entry)



