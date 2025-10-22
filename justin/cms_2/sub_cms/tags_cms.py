from abc import abstractmethod
from typing import List

from justin.cms_2.storage.sqlite.sqlite_database import SQLiteDatabase
from justin.cms_2.storage.sqlite.sqlite_entries import Tag
from justin_utils.util import distinct


class TagsCMS:
    __TAGS_REPLACE_MAP = {
        "#polls": "#poll",
        "#portait": "#portrait",
        "#reports": "#report",
        "#patterns": "#pattern",
        "#nanoreports": "#nanoreport",
        "#initiation": "#init",
    }

    @property
    @abstractmethod
    def db(self) -> SQLiteDatabase:
        pass

    @staticmethod
    def extract_tags(text: str) -> List[str]:
        words = text.split()

        tags = [word for word in words if Tag.is_tag(word)]

        tags = [tag.split("@")[0] for tag in tags]
        tags = [TagsCMS.__TAGS_REPLACE_MAP.get(tag, tag) for tag in tags]
        tags = distinct(tags)

        return tags

    def index_tags(self, text: str) -> None:
        tags = TagsCMS.extract_tags(text)

        existing_tags = self.get_tags()

        tags_mapping = {tag.text: tag for tag in existing_tags}

        tags_entries = [tags_mapping.get(tag) or Tag(text=tag) for tag in tags]

        with self.db.connect():
            self.db.update(*tags_entries)

    def get_tags(self) -> List[Tag]:
        with self.db.connect():
            return self.db.get_entries(Tag)
