from typing import List

from v3_0.actions.named.stage.logic.base.check import Check
from v3_0.shared.metafiles.photoset_metafile import PhotosetMetafile
from v3_0.shared.metafiles.post_metafile import PostStatus, PostMetafile
from v3_0.shared.models.photoset import Photoset


class MetafileStateCheck(Check):
    def __init__(self) -> None:
        super().__init__("metafile check")

    @staticmethod
    def __metafile_required(photoset: Photoset) -> bool:
        return photoset.justin is not None

    @staticmethod
    def __metafile_has_no_group_entries(photoset_metafile: PhotosetMetafile) -> bool:
        return photoset_metafile.posts.empty()

    @staticmethod
    def __group_entry_has_no_post_entries(post_metafiles: List[PostMetafile]) -> bool:
        return len(post_metafiles) == 0

    @staticmethod
    def __metafile_has_not_published_entries(post_metafiles: List[PostMetafile]) -> bool:
        return any(post_metafile.status != PostStatus.PUBLISHED for post_metafile in post_metafiles)

    @staticmethod
    def __photoset_has_folders_not_in_metafile(photoset: Photoset, post_metafiles: List[PostMetafile]) -> bool:
        posted_paths = {post_metafile.path for post_metafile in post_metafiles}

        relative_paths = [subtree.path.relative_to(photoset.path) for subtree in photoset.justin.subtrees]

        return any(path not in posted_paths for path in relative_paths)

    def is_good(self, photoset: Photoset) -> bool:
        if not MetafileStateCheck.__metafile_required(photoset):
            return True

        if not photoset.has_metafile():
            return False

        photoset_metafile = photoset.get_metafile()

        if MetafileStateCheck.__metafile_has_no_group_entries(photoset_metafile):
            return False

        for group_url in photoset_metafile.posts:
            post_metafiles = photoset_metafile.posts[group_url]

            if MetafileStateCheck.__group_entry_has_no_post_entries(post_metafiles) \
                    or MetafileStateCheck.__metafile_has_not_published_entries(post_metafiles) \
                    or MetafileStateCheck.__photoset_has_folders_not_in_metafile(photoset, post_metafiles):
                return False

        return True
