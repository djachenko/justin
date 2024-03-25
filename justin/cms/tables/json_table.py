import json
from pathlib import Path
from typing import Callable, Type

from justin.cms.tables.table import Table, E, K


class JsonTable(Table):
    __ENTRIES_KEY = "entries"

    def __init__(self, path: Path, type_: Type[E], key: Callable[[E], K] = None):
        super().__init__(type_, key)

        self.path = path

    def load(self) -> None:
        if not self.path.exists():
            return

        with self.path.open() as entries_json_file:
            entries_json = json.load(entries_json_file)

            self.entries = [self.type.from_dict(entry_json) for entry_json in entries_json[JsonTable.__ENTRIES_KEY]]

    def save(self) -> None:
        if not self.entries:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)

        entries_json = {
            JsonTable.__ENTRIES_KEY: [entry.as_dict() for entry in self.entries]
        }

        with self.path.open("w", encoding='utf8') as entries_json_file:
            json.dump(entries_json, entries_json_file, indent=4, ensure_ascii=False)
