from csv import DictWriter, DictReader
from pathlib import Path
from typing import Callable, List, Type

from justin.cms.tables.table import Table, E, K


class CsvTable(Table):
    def __init__(self, path: Path, type_: Type[E], key: Callable[[E], K] = None):
        super().__init__(type_, key)

        self.__path = path

    def load(self) -> None:
        if not self.__path.exists():
            return

        with self.__path.open() as entries_csv_file:
            reader = DictReader(entries_csv_file)

            self.entries = [self.type.from_dict(row) for row in reader]

    def save(self) -> None:
        if not self.entries:
            return

        self.__path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames: List[str] = self.entries[0].as_dict().keys()
        rows = [entry.as_dict() for entry in self.entries]

        with self.__path.open("w") as entries_csv_file:
            writer = DictWriter(entries_csv_file, fieldnames)

            writer.writeheader()
            writer.writerows(rows)
