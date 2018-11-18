from pathlib import Path
from typing import List

from v3_0.filesystem.file import File
from v3_0.filesystem.folder_tree.folder_tree import FolderTree


class SingleFolderTree(FolderTree):
    def __init__(self, path: Path) -> None:
        super().__init__(path)

        self.__path = path
        self.__subtrees = {}
        self.__files = []

        for child in path.iterdir():
            if child.is_dir():
                self.__subtrees[child.name] = SingleFolderTree(child)
            elif child.is_file():
                self.files.append(File(child))
            else:
                print("Path not file or dir")

                exit(1)

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def files(self) -> List[File]:
        return self.__files

    @property
    def subtree_names(self) -> List[str]:
        return list(self.__subtrees.keys())

    @property
    def subtrees(self) -> List['FolderTree']:
        return self.__subtree_values

    @property
    def __subtree_values(self) -> List['FolderTree']:
        return list(self.__subtrees.values())

    def __getitem__(self, key: str) -> FolderTree:
        if key in self.__subtrees:
            return self.__subtrees[key]
        else:
            assert False

    def flatten(self) -> List[File]:
        result = self.files

        for subtree in self.__subtree_values:
            result += subtree.flatten()

        return result
