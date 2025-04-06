from dataclasses import dataclass
from datetime import datetime
from typing import Type, Self, Dict, Callable

from justin.cms_2.storage.google_sheets.google_sheets_database import DATETIME_FORMAT, GoogleSheetsEntry, Link
from justin.shared.helpers.utils import Json


@dataclass
class PostEntry(GoogleSheetsEntry):
    post_id: int
    group_id: int
    post_date: datetime
    link: Link
    synced: bool

    @classmethod
    def from_dict(cls: Type[Self], json_object: Json, rules: Dict[type, Callable] = None) -> Self:
        if rules is None:
            rules = {}

        return super().from_dict(json_object, rules | {
            datetime: lambda json: datetime.strptime(json, DATETIME_FORMAT),
        })

    def as_dict(self) -> Json:
        result = super().as_dict()

        result["post_date"] = self.post_date.strftime(DATETIME_FORMAT)

        return result
