from abc import abstractmethod
from typing import Dict, List, Union, Type

from justin.shared.metafile import Json, RootMetafile, GroupMetafile
from justin_utils.json_migration import JsonMigration, JsonObject, Version
from justin_utils.singleton import Singleton


class PostFormatMigration(JsonMigration):
    __URL_MAPPING = {
        "djachenko": 100568944
    }

    @property
    def version(self) -> Version:
        return 1

    def migrate(self, json_object: JsonObject) -> None:
        posts_mapping: Dict[str, List[Dict[str, Union[str, int]]]] = json_object["posts"]

        for key in posts_mapping:
            self.rename(posts_mapping, key, PostFormatMigration.__URL_MAPPING.get(key, key))


class PostStatusMigration(JsonMigration):
    __STATUS_RENAME_MAPPING = {
        "posted": "published"
    }

    @property
    def version(self) -> Version:
        return 2

    def migrate(self, json_object: JsonObject) -> None:
        for group_posts in json_object["posts"].values():
            for post in group_posts:
                post["post_status"] = PostStatusMigration.__STATUS_RENAME_MAPPING.get(
                    post["post_status"],
                    post["post_status"]
                )

