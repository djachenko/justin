import json
from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, List, Union

Json = Union[
    Dict[str, 'Json'],
    List['Json'],
    str,
]


class Metafile:
    @abstractmethod
    def encode(self) -> Json:
        pass

    @classmethod
    @abstractmethod
    def decode(cls, d: Json) -> 'Metafile':
        pass

    @classmethod
    def read(cls, path: Path):
        if path.exists() and path.stat().st_size > 0:
            with path.open() as metafile_file:
                json_dict = json.load(metafile_file)
        else:
            json_dict = {}

        return cls.decode(json_dict)

    def write(self, path: Path):
        with path.open(mode="w") as metafile_file:
            json_dict = self.encode()

            json.dump(json_dict, metafile_file, indent=4)


class PostStatus(Metafile, Enum):
    SCHEDULED = "scheduled"
    PUBLISHED = "posted"

    @classmethod
    def decode(cls, string: Json) -> 'PostStatus':
        string = string.lower()

        for status in PostStatus:
            if string == status.value:
                return status

        return PostStatus.SCHEDULED

    def encode(self) -> Json:
        return self.value


class PostMetafile(Metafile):
    __PATH_KEY = "path"
    __POST_ID_KEY = "id"
    __STATUS_KEY = "post_status"

    # cover
    # grid

    def __init__(self, path: Path, post_id: int, status: PostStatus) -> None:
        super().__init__()

        self.path = path
        self.post_id = post_id
        self.status = status

    def encode(self) -> Json:
        return {
            PostMetafile.__PATH_KEY: self.path.as_posix(),
            PostMetafile.__POST_ID_KEY: self.post_id,
            PostMetafile.__STATUS_KEY: self.status.encode(),
        }

    @classmethod
    def decode(cls, d: Json) -> 'PostMetafile':
        if PostMetafile.__STATUS_KEY in d:
            status = PostStatus.decode(d[PostMetafile.__STATUS_KEY])
        else:
            status = PostStatus.SCHEDULED

        return PostMetafile(
            path=Path(d[PostMetafile.__PATH_KEY]),
            post_id=d[PostMetafile.__POST_ID_KEY],
            status=status
        )


class PhotosetMetafile(Metafile):
    __POSTS_KEY = "posts"

    def __init__(self, posts: Dict[str, List[PostMetafile]]) -> None:
        super().__init__()

        self.posts = posts

    @classmethod
    def decode(cls, d: Json) -> 'PhotosetMetafile':
        return PhotosetMetafile(
            posts={k: [PostMetafile.decode(post_json) for post_json in v] for k, v
                   in d[PhotosetMetafile.__POSTS_KEY].items()}
        )

    def encode(self) -> Json:
        return {
            PhotosetMetafile.__POSTS_KEY: {k: [post.encode() for post in v] for k, v in self.posts.items()}
        }
