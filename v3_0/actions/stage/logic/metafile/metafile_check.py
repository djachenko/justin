from v3_0.actions.stage.logic.base.check import Check
from v3_0.shared.metafiles.post_metafile import PostStatus
from v3_0.shared.models.photoset import Photoset


class MetafileCheck(Check):
    def __init__(self) -> None:
        super().__init__("metafile check")

    def is_good(self, photoset: Photoset) -> bool:
        if photoset.justin is None:
            return True

        if not photoset.has_metafile():
            return False

        photoset_metafile = photoset.get_metafile()

        if photoset_metafile.posts.empty():
            return False

        for group_url in photoset_metafile.posts:
            post_metafiles = photoset_metafile.posts[group_url]

            if len(post_metafiles) == 0:
                return False

            for post_metafile in post_metafiles:
                if post_metafile.status != PostStatus.PUBLISHED:
                    return False

        return True
