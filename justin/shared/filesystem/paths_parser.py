from pathlib import Path
from typing import List

from justin.shared.filesystem.file import File
from justin.shared.filesystem.folder_tree import FolderTree
from justin.shared.filesystem.path_based import PathBased


class PathsParser:
    @staticmethod
    def parse(paths: List[Path]) -> List[PathBased]:
        result = []

        for path in paths:
            if path.is_file():
                result.append(File(path))
            elif path.is_dir():
                result.append(FolderTree(path))
            else:
                assert False

        return result
