from abc import abstractmethod
from collections import defaultdict
from typing import List

from justin.cms_2.storage.sqlite.sqlite_database import SQLiteDatabase
from justin.cms_2.storage.sqlite.sqlite_entries import PostToTag
from justin.cms_2.sub_cms.tags_cms import TagsCMS


class PostsToTagsCMS:
    @property
    @abstractmethod
    def db(self) -> SQLiteDatabase:
        pass

    @property
    @abstractmethod
    def tags_cms(self) -> TagsCMS:
        pass

    def index_post_to_tags(self, post_text: str, post_id: int, group_id: int) -> None:
        existing_tags = self.tags_cms.get_tags()
        tags_mapping = {tag.text: tag for tag in existing_tags}

        post_tags = TagsCMS.extract_tags(post_text)
        post_tags_ids = [tags_mapping[tag_text].tag_id for tag_text in post_tags]

        self.link_post_to_tags(post_id, group_id, *post_tags_ids)

    def link_post_to_tags(self, post_id: int, group_id: int, *tag_ids: int) -> None:
        post_to_tags = [PostToTag(
            group_id=group_id,
            post_id=post_id,
            tag_id=tag_id
        ) for tag_id in tag_ids]

        with self.db.connect():
            self.db.update(*post_to_tags)

    def unlink_post_to_tags(self, post_id: int, group_id: int, *tag_ids: int) -> None:
        post_to_tags = [PostToTag(
            group_id=group_id,
            post_id=post_id,
            tag_id=tag_id
        ) for tag_id in tag_ids]

        with self.db.connect():
            self.db.delete(*post_to_tags)

    def __get_posts_to_tags(self) -> List[PostToTag]:
        with self.db.connect():
            return self.db.get_entries(PostToTag)

    def get_tag_ids_of_post(self, post_id: int, group_id: int) -> List[int]:
        return [ptt.tag_id for ptt in self.__get_posts_to_tags() if ptt.post_id == post_id and ptt.group_id == group_id]

    def tag_usage_count(self, tag_id: int) -> int:
        posts_to_tags = self.__get_posts_to_tags()

        stats = defaultdict(lambda: 0)

        for post_to_tag in posts_to_tags:
            stats[post_to_tag.tag_id] += 1

        return stats[tag_id]
