from pathlib import Path

from justin.cms_2.storage.sqlite.sqlite_database import SQLiteDatabase
from justin.cms_2.sub_cms.people_cms import PeopleCMS
from justin.cms_2.sub_cms.photosets_cms import PhotosetsCMS
from justin.cms_2.sub_cms.posts_to_tags_cms import PostsToTagsCMS
from justin.cms_2.sub_cms.posts_cms import PostsCMS
from justin.cms_2.sub_cms.synced_tags_cms import SyncedTagsCMS
from justin.cms_2.sub_cms.tags_cms import TagsCMS


class SQLiteCMS(PhotosetsCMS, PostsCMS, PostsToTagsCMS, TagsCMS, SyncedTagsCMS, PeopleCMS):
    def __init__(self, root: Path):
        self.__db = SQLiteDatabase(root, "justin.db")

    @property
    def db(self) -> SQLiteDatabase:
        return self.__db

    @property
    def tags_cms(self) -> TagsCMS:
        return self

    @property
    def post_to_tags_cms(self) -> PostsToTagsCMS:
        return self
