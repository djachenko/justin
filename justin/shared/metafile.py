import json
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Union, ClassVar

from justin_utils.json_migration import JsonMigrator

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

            JsonMigrator.instance().migrate(json_dict)
        else:
            json_dict = {}

        return cls.decode(json_dict)

    def write(self, path: Path):
        with path.open(mode="w") as metafile_file:
            json_dict = self.encode()

            json.dump(json_dict, metafile_file, indent=4)


class PostStatus(Metafile, Enum):
    SCHEDULED = "scheduled"
    PUBLISHED = "published"

    @classmethod
    def decode(cls, string: Json) -> 'PostStatus':
        string = string.upper()

        return PostStatus[string]

    def encode(self) -> Json:
        return self.value


@dataclass
class PostMetafile(Metafile):
    __PATH_KEY: ClassVar[str] = "path"
    __POST_ID_KEY: ClassVar[str] = "id"
    __STATUS_KEY: ClassVar[str] = "post_status"
    __GROUP_ID_KEY: ClassVar[str] = "group_id"

    path: Path
    post_id: int
    status: PostStatus

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
            status=status,
        )


@dataclass
class PhotosetMetafile(Metafile):
    __POSTS_KEY: ClassVar[str] = "posts"

    posts: Dict[int, List[PostMetafile]]

    @classmethod
    def decode(cls, d: Json) -> 'PhotosetMetafile':
        group_posts_mapping = {}

        for group_id, group_posts in d.get(PhotosetMetafile.__POSTS_KEY, {}).items():
            group_posts_mapping[int(group_id)] = [PostMetafile.decode(group_post) for group_post in group_posts]

        return PhotosetMetafile(
            posts=group_posts_mapping
        )

    def encode(self) -> Json:
        jsons_mapping = {}

        for group_id, posts in self.posts.items():
            jsons_mapping[group_id] = [post.encode() for post in posts]

        return {
            PhotosetMetafile.__POSTS_KEY: jsons_mapping
        }
