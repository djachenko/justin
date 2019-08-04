from v3_0.actions.archive import TreeBased
from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree


class Category(TreeBased):
    def __init__(self, tree: FolderTree) -> None:
        super().__init__(tree)
