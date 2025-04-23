from typing import Iterable

from justin.actions.stage.logic.base import Problem, DestinationsAwareCheck
from justin.shared.filesystem import Folder
from justin.shared.metafile import PostMetafile, GroupMetafile, PostStatus, PersonMetafile


class MetafilesExistCheck(DestinationsAwareCheck):
    def check_post_metafile(self, folder: Folder) -> Iterable[Problem]:
        if not PostMetafile.has(folder):
            return [f"Folder {folder.path} doesn't have post metafile"]

        return []

    def check_group_metafile(self, folder: Folder) -> Iterable[Problem]:
        if not GroupMetafile.has(folder):
            return [f"Folder {folder.path} doesn't have group metafile"]

        return []

    def check_person_metafile(self, folder: Folder) -> Iterable[Problem]:
        if not PersonMetafile.has(folder):
            return [f"Folder {folder.path} doesn't have person metafile"]

        return []


class MetafilesPublishedCheck(DestinationsAwareCheck):

    def check_group_metafile(self, folder: Folder) -> Iterable[Problem]:
        return []

    def check_post_metafile(self, folder: Folder) -> Iterable[Problem]:
        post_metafile = PostMetafile.get(folder)

        if post_metafile.status != PostStatus.PUBLISHED:
            return [f"Post at {folder.path} is not published."]

        return []

    def check_person_metafile(self, folder: Folder) -> Iterable[Problem]:
        person_metafile = PersonMetafile.get(folder)

        for comment_metafile in person_metafile.comments:
            if comment_metafile.status != PostStatus.PUBLISHED:
                return [f"{folder.name}'s photos not fully sent"]

        return []
