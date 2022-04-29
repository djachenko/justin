from abc import abstractmethod

from justin.actions.named.stage.logic.base import Check
from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile2 import PostMetafile, GroupMetafile, PostStatus
from justin.shared.models.photoset import Photoset


class DestinationsAwareCheck(Check):
    @abstractmethod
    def check_post_metafile(self, folder: FolderTree) -> bool:
        pass

    @abstractmethod
    def check_group_metafile(self, folder: FolderTree) -> bool:
        pass

    def is_good(self, photoset: Photoset) -> bool:
        if photoset.justin is not None:
            if not self.check_group_metafile(photoset.justin):
                return False

            for name_folder in photoset.justin.subtrees:
                for post_folder in folder_tree_parts(name_folder):
                    if not self.check_post_metafile(post_folder):
                        return False

        def check_event(event_folder: FolderTree) -> bool:
            if not self.check_group_metafile(event_folder):
                return False

            for post_folder_ in folder_tree_parts(event_folder):
                if not self.check_post_metafile(post_folder_):
                    return False

        if photoset.closed is not None:
            for name_folder in photoset.closed.subtrees:
                check_event(name_folder)

        if photoset.meeting is not None:
            check_event(photoset.meeting)

        return True


class MetafilesExistCheck(DestinationsAwareCheck):
    def check_post_metafile(self, folder: FolderTree) -> bool:
        return folder.has_metafile(PostMetafile)

    def check_group_metafile(self, folder: FolderTree) -> bool:
        return folder.has_metafile(GroupMetafile)


class MetafilesPublishedCheck(DestinationsAwareCheck):

    def check_group_metafile(self, folder: FolderTree) -> bool:
        return True

    def check_post_metafile(self, folder: FolderTree) -> bool:
        post_metafile = folder.get_metafile(PostMetafile)

        return post_metafile.status == PostStatus.PUBLISHED


class MetafileStateCheck(Check):
    def __init__(self) -> None:
        super().__init__("metafile check")

        self.__inner = [
            MetafilesExistCheck("metafiles exist"),
            MetafilesPublishedCheck("metafiles published"),
        ]

    def is_good(self, photoset: Photoset) -> bool:
        return all(inner_check.is_good(photoset) for inner_check in self.__inner)
