from typing import List

from v3_0.shared.metafiles.metafile import Metafile
from v3_0.shared.metafiles.post_metafile import PostMetafile


class PhotosetMetafile(Metafile):
    __POSTS_KEY = "posts"

    def __init__(self, posts: List[PostMetafile]) -> None:
        super().__init__()

        self.posts = posts

    def to_dict(self) -> dict:
        return {
            "posts": [post.to_dict() for post in self.posts]
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'PhotosetMetafile':
        posts_array = d.get(PhotosetMetafile.__POSTS_KEY, [])

        posts = [PostMetafile.from_dict(i) for i in posts_array]

        return cls(posts)
