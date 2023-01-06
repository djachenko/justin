from typing import Iterable

from justin.actions.stage.logic.base import Problem, DestinationsAwareCheck
from justin.shared.filesystem import Folder
from justin.shared.metafile import PostMetafile, GroupMetafile, PostStatus, PersonMetafile, MetaFolder


class MetafilesExistCheck(DestinationsAwareCheck):
    def check_post_metafile(self, folder: MetaFolder) -> Iterable[Problem]:
        if not folder.has_metafile(PostMetafile):
            return [f"Folder {folder.path} doesn't have post metafile"]

        return []

    def check_group_metafile(self, folder: MetaFolder) -> Iterable[Problem]:
        if not folder.has_metafile(GroupMetafile):
            return [f"Folder {folder.path} doesn't have group metafile"]

        return []

    def check_person_metafile(self, folder: MetaFolder) -> Iterable[Problem]:
        if not folder.has_metafile(PersonMetafile):
            return [f"Folder {folder.path} doesn't have person metafile"]

        return []


class MetafilesPublishedCheck(DestinationsAwareCheck):

    def check_group_metafile(self, folder: Folder) -> Iterable[Problem]:
        return []

    def check_post_metafile(self, folder: MetaFolder) -> Iterable[Problem]:
        post_metafile = folder.get_metafile(PostMetafile)

        if post_metafile.status != PostStatus.PUBLISHED:
            return [f"Post at {folder.path} is not published."]

        return []

    def check_person_metafile(self, folder: MetaFolder) -> Iterable[Problem]:
        person_metafile = folder.get_metafile(PersonMetafile)

        for comment_metafile in person_metafile.comments:
            if comment_metafile.status != PostStatus.PUBLISHED:
                return [f"{folder.name}'s photos not fully sent"]

        return []
