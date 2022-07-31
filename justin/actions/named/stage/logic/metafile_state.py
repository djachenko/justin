from abc import abstractmethod
from typing import Iterable

from justin.actions.named.stage.logic.base import Check, MetaCheck, Problem
from justin.shared.filesystem import FolderTree
from justin.shared.helpers.parts import folder_tree_parts
from justin.shared.metafile import PostMetafile, GroupMetafile, PostStatus
from justin.shared.models.photoset import Photoset


class DestinationsAwareCheck(Check):
    @abstractmethod
    def check_post_metafile(self, folder: FolderTree) -> Iterable[Problem]:
        pass

    @abstractmethod
    def check_group_metafile(self, folder: FolderTree) -> Iterable[Problem]:
        pass

    def get_problems(self, photoset: Photoset) -> Iterable[Problem]:
        problems = []

        if photoset.justin is not None:
            problems += self.check_group_metafile(photoset.justin)

            for name_folder in photoset.justin.subtrees:
                for post_folder in folder_tree_parts(name_folder):
                    problems += self.check_post_metafile(post_folder)

        def check_event(event_folder: FolderTree) -> Iterable[Problem]:
            local_problems = self.check_group_metafile(event_folder)

            for post_folder_ in folder_tree_parts(event_folder):
                local_problems += self.check_post_metafile(post_folder_)

            return local_problems

        if photoset.closed is not None:
            for name_folder in photoset.closed.subtrees:
                problems += check_event(name_folder)

        if photoset.meeting is not None:
            problems += check_event(photoset.meeting)

        return problems


class MetafilesExistCheck(DestinationsAwareCheck):
    def check_post_metafile(self, folder: FolderTree) -> Iterable[Problem]:
        if not folder.has_metafile(PostMetafile):
            return [f"Folder {folder.path} doesn't have post metafile"]

        return []

    def check_group_metafile(self, folder: FolderTree) -> Iterable[Problem]:
        if not folder.has_metafile(GroupMetafile):
            return [f"Folder {folder.path} doesn't have group metafile"]

        return []


class MetafilesPublishedCheck(DestinationsAwareCheck):

    def check_group_metafile(self, folder: FolderTree) -> Iterable[Problem]:
        return []

    def check_post_metafile(self, folder: FolderTree) -> Iterable[Problem]:
        post_metafile = folder.get_metafile(PostMetafile)

        if post_metafile.status != PostStatus.PUBLISHED:
            return [f"Metafile at {folder.path} is not published."]

        return []


class MetafileStateCheck(MetaCheck):
    def __init__(self) -> None:
        super().__init__("metafile_check", [
            MetafilesExistCheck("metafiles exist"),
            MetafilesPublishedCheck("metafiles published"),
        ])
