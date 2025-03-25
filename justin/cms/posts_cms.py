from abc import ABC
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Type, List

from justin.cms.base_cms import BaseCMS
from justin.cms.tables.csv_table import CsvTable
from justin.cms.tables.table import Table, Entry, T
from justin.shared.helpers.utils import Json
from pyvko.aspects.posts import Posts, Post
from pyvko.attachment.photo import Photo
from pyvko.pyvko_main import Pyvko


@dataclass
class PostEntry(Entry):
    @classmethod
    def from_dict(cls: Type[T], json_object: Json) -> T:
        entry = super().from_dict(json_object)

        entry.tags = json_object["tags"]

        return entry

    group_id: int
    post_id: int
    tags: List[str]
    text: str

    @property
    def complex_id(self) -> str:
        return f"{self.group_id}_{self.post_id}"


class PostsCMS(BaseCMS, ABC):
    __TAGS_REPLACE_MAP: Dict[str, str] = {
        "#polls": "#poll",
        "#portait": "#portrait",
        "#reports": "#report",
        "#patterns": "#pattern",
        "#nanoreports": "#nanoreport",
        "#initiation": "#init",
    }

    @property
    @lru_cache()
    def posts(self) -> Table[PostEntry, str]:
        return CsvTable(self.root / "posts.csv", PostEntry, lambda x: x.complex_id)

    @staticmethod
    def __get_index_text(post: Post) -> str:
        index_texts = [post.text]

        photos = [attach for attach in post.attachments if isinstance(attach, Photo)]

        for photo in photos:
            index_texts += photo.text

        return " ".join(index_texts)

    @staticmethod
    def __extract_tags(post: Post) -> List[str]:
        words = PostsCMS.__get_index_text(post).split()

        tags = [word for word in words if word.startswith("#") and "@" in word]

        tags = [tag.split("@")[0] for tag in tags]
        tags = [PostsCMS.__TAGS_REPLACE_MAP.get(tag, tag) or tag for tag in tags]

        return tags

    def index_post(self, post: Post, group_id: int) -> None:
        text = post.text
        tags = PostsCMS.__extract_tags(post)
        post_id = post.id

        entry = PostEntry(
            group_id=group_id,
            post_id=post_id,
            text=text,
            tags=tags
        )

        self.posts.update(entry)
        self.posts.save()

    def index_group(self, identifier: str, pyvko: Pyvko) -> None:
        group = pyvko.get(identifier)

        assert isinstance(group, Posts)

        group_id = group.id
        posts = group.get_posts()

        self.posts.load()

        for post in posts:
            self.index_post(post, group_id)

        self.posts.save()
