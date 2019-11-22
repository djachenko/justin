from pathlib import Path
from typing import List, Optional, Dict

from v3_0.shared.filesystem.file import File
from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree


class SingleFolderTree(FolderTree):
    # noinspection PyTypeChecker
    def __init__(self, path: Path) -> None:
        super().__init__(path)

        self.__backing_subtrees: Dict[str, FolderTree] = None
        self.__files: List[File] = None

    @property
    def __subtrees(self) -> Dict[str, FolderTree]:
        if self.__backing_subtrees is None:
            self.refresh()

        return self.__backing_subtrees

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def files(self) -> List[File]:
        if self.__files is None:
            self.refresh()

        return self.__files

    @property
    def subtree_names(self) -> List[str]:
        return list(self.__subtrees.keys())

    @property
    def subtrees(self) -> List[FolderTree]:
        return list(self.__subtrees.values())

    def __getitem__(self, key: str) -> Optional[FolderTree]:
        return self.__subtrees.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self.subtrees

    def flatten(self) -> List[File]:
        result = self.files.copy()

        for subtree in self.subtrees:
            result += subtree.flatten()

        return result

    def refresh(self):
        self.__backing_subtrees = {}
        self.__files = []

        for child in self.path.iterdir():
            if child.is_dir():
                child_tree = SingleFolderTree(child)

                if len(child_tree.flatten()) > 0:
                    self.__subtrees[child.name] = child_tree
                else:
                    child.rmdir()

            elif child.is_file():
                if child.name.lower() == ".DS_store".lower():
                    child.unlink()
                else:
                    self.files.append(File(child))
            else:
                print("Path is neither file nor dir")

                exit(1)
