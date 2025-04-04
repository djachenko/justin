from dataclasses import dataclass
from datetime import datetime
from typing import List, Type, Self, Dict, Callable

from justin.cms.google_sheets_database import DATETIME_FORMAT, GoogleSheetsEntry, Link
from justin.shared.helpers.utils import fromdict, Json


@dataclass
class PostEntry(GoogleSheetsEntry):
    post_id: int
    group_id: int
    post_date: datetime
    link: Link

    @classmethod
    def from_dict(cls: Type[Self], json_object: Json, rules: Dict[type, Callable] = None) -> Self:
        if rules is None:
            rules = {}

        return super().from_dict(json_object, rules | {
            datetime: lambda json: datetime.strptime(json, DATETIME_FORMAT),
        })
        # entry.post_date = datetime.strptime(json_object["post_date"], DATETIME_FORMAT)

        # return entry

    def as_dict(self) -> Json:
        result = super().as_dict()

        result["post_date"] = self.post_date.strftime(DATETIME_FORMAT)

        return result
