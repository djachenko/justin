from dataclasses import dataclass
from datetime import datetime
from sqlite3 import Cursor
from typing import Dict, Any, Self, Type, Callable

from justin.cms_2.storage.sqlite.sqlite_database import SQLiteEntry
from pyvko.shared.utils import Json


@dataclass
class Person(SQLiteEntry):
    folder: str
    name: str
    vk_id: int | None

    @classmethod
    def type(cls) -> str:
        return "People"


@dataclass
class PersonPhotos(SQLiteEntry):
    folder: str
    photoset: str
    count: int


class MyPeople(PersonPhotos):
    pass


class Drive(PersonPhotos):
    pass


class Closed(PersonPhotos):
    pass


@dataclass
class Photoset(SQLiteEntry):
    folder: str

    @classmethod
    def type(cls) -> str:
        return "Photosets"


@dataclass
class Post(SQLiteEntry):
    group_id: int
    post_id: int
    date: datetime
    text: str | None

    @classmethod
    def type(cls) -> str:
        return "Posts"

    @classmethod
    def from_dict(cls, json_object: Json, rules: Dict[Type, Callable] = None) -> Self:
        rules = rules or {}

        return super().from_dict(json_object, rules | {
            datetime: lambda json: datetime.fromtimestamp(json)
        })

    def as_dict(self) -> Dict[str, Any]:
        result = super().as_dict()

        result["date"] = self.date.timestamp()

        return result

    @classmethod
    def from_cursor(cls, cursor: Cursor, row) -> Self:
        result = super().from_cursor(cursor, row)

        return result


@dataclass
class Tag(SQLiteEntry):
    text: str
    tag_id: int | None = None

    @property
    def clean_text(self) -> str:
        return self.text.strip("#")

    @classmethod
    def type(cls) -> str:
        return "Tags"

    def as_dict(self) -> Dict[str, Any]:
        result = super().as_dict()

        if self.tag_id is None:
            del result["tag_id"]

        return result


@dataclass
class SyncedTagsPost(SQLiteEntry):
    post_id: int
    group_id: int

    @classmethod
    def type(cls) -> str:
        return "SyncedTags"


@dataclass
class PostToTag(SQLiteEntry):
    group_id: int
    post_id: int
    tag_id: int

    @classmethod
    def type(cls) -> str:
        return "Posts2Tags"
