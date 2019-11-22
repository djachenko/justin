from typing import List, Dict

from v3_0.shared.metafiles.metafile import Metafile
from v3_0.shared.metafiles.post_metafile import PostMetafile


class GroupsMetafile(Metafile):
    def __init__(self, group_mapping: Dict[str, List[PostMetafile]]) -> None:
        super().__init__()

        self.__mapping = group_mapping

    def __getitem__(self, url: str) -> List[PostMetafile]:
        if url not in self.__mapping:
            return []

        return self.__mapping[url]

    def __setitem__(self, url: str, posts: List[PostMetafile]) -> None:
        self.__mapping[url] = posts

    def __iter__(self):
        return iter(self.__mapping)

    def empty(self) -> bool:
        return len(self.__mapping) == 0

    def to_dict(self) -> dict:
        future_json = {}

        for group_url, group_posts in self.__mapping.items():
            posts_jsons = [post.to_dict() for post in group_posts]

            future_json[group_url] = posts_jsons

        return future_json

    @classmethod
    def from_dict(cls, d: dict) -> 'GroupsMetafile':
        mapping = {}

        for group_url, posts_list in d.items():
            posts = [PostMetafile.from_dict(post_json) for post_json in posts_list]

            mapping[group_url] = posts

        # noinspection PyTypeChecker
        return cls(mapping)
