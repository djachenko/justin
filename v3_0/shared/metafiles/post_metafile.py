from enum import Enum
from pathlib import Path
from typing import Optional

from v3_0.shared.metafiles.metafile import Metafile


class PostStatus(Enum):
    SCHEDULED = "scheduled"
    PUBLISHED = "posted"

    @classmethod
    def from_string(cls, string: str) -> Optional['PostStatus']:
        string = string.lower()

        for status in PostStatus:
            if string == status.value:
                return status

        return None

    def to_string(self) -> str:
        return self.value


class PostMetafile(Metafile):
    VERSION = 0

    __VERSION_KEY = "version"
    __PATH_KEY = "path"
    __POST_ID_KEY = "id"
    __GROUP_ID_KEY = "group_url"
    __STATUS_KEY = "post_status"

    def __init__(self, path: Path, post_id: int, group_url: str, status: PostStatus) -> None:
        super().__init__()

        self.path = path
        self.group_url = group_url
        self.post_id = post_id
        self.status = status

    def to_dict(self) -> dict:
        return {
            PostMetafile.__GROUP_ID_KEY: self.group_url,
            PostMetafile.__PATH_KEY: str(self.path),
            PostMetafile.__POST_ID_KEY: self.post_id,
            PostMetafile.__STATUS_KEY: self.status.to_string(),
            PostMetafile.__VERSION_KEY: PostMetafile.VERSION
        }

    @classmethod
    def from_dict(cls, json: dict) -> 'PostMetafile':
        if PostMetafile.__GROUP_ID_KEY in json:
            group_url = json[PostMetafile.__GROUP_ID_KEY]
        else:
            group_url = "pyvko_test2"

        post_id = json[PostMetafile.__POST_ID_KEY]
        path = Path(json[PostMetafile.__PATH_KEY])

        if PostMetafile.__STATUS_KEY in json:
            status = PostStatus.from_string(json[PostMetafile.__STATUS_KEY])
        else:
            status = PostStatus.SCHEDULED

        return PostMetafile(
            path=path,
            post_id=post_id,
            group_url=group_url,
            status=status
        )
