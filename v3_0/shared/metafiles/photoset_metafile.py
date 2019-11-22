from v3_0.shared.metafiles.groups_metafile import GroupsMetafile
from v3_0.shared.metafiles.metafile import Metafile


class PhotosetMetafile(Metafile):
    __POSTS_KEY = "posts"

    def __init__(self, posts: GroupsMetafile) -> None:
        super().__init__()

        self.__posts = posts

    @property
    def posts(self) -> GroupsMetafile:
        return self.__posts

    def to_dict(self) -> dict:
        return {
            "posts": self.posts.to_dict()
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'PhotosetMetafile':
        posts_dict = d.get(PhotosetMetafile.__POSTS_KEY, {})

        posts = GroupsMetafile.from_dict(posts_dict)

        return cls(posts)
