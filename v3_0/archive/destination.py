from v3_0.archive.category import Category
from v3_0.archive.tree_based import TreeBased
from v3_0.shared.filesystem.folder_tree.folder_tree import FolderTree


class Destination(TreeBased):
    def __init__(self, tree: FolderTree) -> None:
        super().__init__(tree)

        self.__categories = [Category(subtree) for subtree in tree.subtrees]

    @property
    def has_categories(self):
        return True

    def get_category(self, name: str) -> Optional[Category]:
        categories_with_name = [cat for cat in self.__categories if cat.name == name]

        assert len(categories_with_name) < 2

        if len(categories_with_name) == 1:
            return categories_with_name[0]
        else:
            return None
