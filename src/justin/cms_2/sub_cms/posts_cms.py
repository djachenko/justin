from abc import abstractmethod
from typing import List

from justin.cms_2.storage.sqlite.sqlite_database import SQLiteDatabase
from justin.cms_2.storage.sqlite.sqlite_entries import Post as PostEntry
from justin.cms_2.sub_cms.posts_to_tags_cms import PostsToTagsCMS
from justin.cms_2.sub_cms.tags_cms import TagsCMS
from pyvko.aspects.posts import Posts, Post
from pyvko.attachment.photo import Photo
from pyvko.pyvko_main import Pyvko


class PostsCMS:
    @property
    @abstractmethod
    def db(self) -> SQLiteDatabase:
        pass

    @property
    @abstractmethod
    def tags_cms(self) -> TagsCMS:
        pass

    @property
    @abstractmethod
    def post_to_tags_cms(self) -> PostsToTagsCMS:
        pass

    @staticmethod
    def __get_index_text(post: Post) -> str:
        photos = [attach for attach in post.attachments if isinstance(attach, Photo)]

        photo_texts = [photo.text for photo in photos]
        index_texts = [post.text] + photo_texts

        index_texts = [text for text in index_texts if text]

        return " ".join(index_texts)

    def index_group(self, identifier: str, pyvko: Pyvko) -> None:
        group = pyvko.get(identifier)

        assert isinstance(group, Posts)

        group_id = group.id
        posts = group.get_posts()

        for post in posts:
            self.__index_post(post, group_id)

    def __index_post(self, post: Post, group_id: int) -> None:
        self.__update_post_entry(post, group_id)

        text = PostsCMS.__get_index_text(post)

        self.tags_cms.index_tags(text)
        self.post_to_tags_cms.index_post_to_tags(text, post.post_id, group_id)

    def get_indexed_posts(self) -> List[PostEntry]:
        with self.db.connect():
            return self.db.get_entries(PostEntry)

    def __update_post_entry(self, post: Post, group_id: int) -> None:
        with self.db.connect():
            self.db.update(PostEntry(
                group_id=group_id,
                post_id=post.id,
                text=post.text,
                date=post.date
            ))
