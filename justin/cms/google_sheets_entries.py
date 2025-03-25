from dataclasses import dataclass
from datetime import datetime
from typing import List, Type, Self, Dict, Callable

from justin.cms.google_sheets_database import DATETIME_FORMAT, GoogleSheetsEntry
from justin.shared.helpers.utils import fromdict, Json

Link = str

@dataclass
class PostEntry(GoogleSheetsEntry):
    post_id: int
    group_id: int
    post_date: datetime
    # link: Link

    @property
    def link(self):
        return f"https://vk.com/wall{self.group_id}_{self.post_id}"

    @classmethod
    def from_dict(cls: Type[Self], json_object: Json, rules: Dict[type, Callable] = None) -> Self:
        if rules is None:
            rules = {}

        entry: PostEntry = super().from_dict(json_object, rules)
        # entry.tags = json_object["tags"].split(", ")
        entry.post_date = datetime.strptime(json_object["post_date"], DATETIME_FORMAT)

        # tags_list: List[str] = []
        # entry.tags = []
        #
        # for tag in tags_list:
        #     if json_object[tag]:
        #         entry.tags.append(tag)

        return entry

    def as_dict(self) -> Json:
        result = super().as_dict()

        result["post_date"] = self.post_date.strftime(DATETIME_FORMAT)

        # del result["state"]
        # del result["timer_id"]

        return result
