import sqlite3
from abc import ABC
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, fields, asdict
from functools import cache
from pathlib import Path
from sqlite3 import Cursor, Row, Connection
from typing import TypeVar, List, Type, Self, Iterable, Any, Dict, Callable

from justin.shared.helpers.utils import fromdict
from justin_utils.util import group_by
from pyvko.shared.utils import Json


@dataclass
class SQLiteEntry(ABC):
    @classmethod
    def type(cls) -> str:
        return cls.__name__

    @classmethod
    def from_dict(cls, json_object: Json, rules: Dict[Type, Callable] = None) -> Self:
        # return cls(**json_object)
        return fromdict(json_object, cls, rules)

    @classmethod
    def from_cursor(cls, cursor: Cursor, row) -> Self:
        object_mapping = dict(zip([d[0] for d in cursor.description], row))

        # noinspection PyArgumentList
        return cls(**object_mapping)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def diff(self, other: Self) -> Dict[str, Any]:
        self_dict = self.as_dict()
        other_dict = other.as_dict()

        assert self_dict.keys() == other_dict.keys()

        diff = {}

        for key in self_dict:
            if self_dict[key] != other_dict[key]:
                diff[key] = self_dict[key]

        return diff


T = TypeVar("T", bound=SQLiteEntry)


class SQLiteDatabase:
    def __init__(self, root: Path, file_name: str = "justin.db") -> None:
        self.__db_path = root / file_name
        self.__db: Connection | None = None

        self.__cache: Dict[Type[T], List[T]] = {}

    @contextmanager
    def connect(self) -> None:
        self.__db = sqlite3.connect(self.__db_path)

        yield

        self.__db.commit()
        self.__db.close()

        self.__db = None

    def __drop_cache(self, cls: Type[T]) -> None:
        del self.__cache[cls]

    def get_entries(self, cls: Type[T]) -> List[T]:
        if cls not in self.__cache:
            query = f"SELECT * FROM {cls.type()}"

            cursor = self.__db.execute(query)
            fieldnames = tuple(d[0] for d in cursor.description)

            def row_factory(_, row):
                row_dict = dict(zip(fieldnames, row))

                return cls.from_dict(row_dict)

            cursor.row_factory = row_factory

            self.__cache[cls] = cursor.fetchall()

        return self.__cache[cls].copy()

    @cache
    def __pk(self, table: str) -> List[str]:
        cursor = self.__db.execute(f"PRAGMA table_info({table});")
        cursor.row_factory = Row
        columns_descriptions = cursor.fetchall()

        pk = []

        for column_description in columns_descriptions:
            if column_description["pk"]:
                pk.append(column_description["name"])

        return pk

    @cache
    def __insert_query(self, cls: Type[T], field_to_insert: Iterable[str] | None = None) -> str:
        table_name = cls.type()
        fields_ = fields(cls)

        field_names = [field.name for field in fields_]

        if field_to_insert:
            field_names = [name for name in field_names if name in field_to_insert]

        columns = ", ".join(field_names)
        parameters = ", ".join(f":{name}" for name in field_names)

        return f"INSERT INTO {table_name} ({columns}) VALUES({parameters})"

    @cache
    def __update_query(self, cls: Type[T], fields_to_change: Iterable[str] | None = None) -> str:
        table_name = cls.type()
        fields_ = fields(cls)

        pk = self.__pk(table_name)

        field_names = [field.name for field in fields_]

        if fields_to_change:
            assert not any(key in fields_to_change for key in pk)

            field_names = [name for name in field_names if name in fields_to_change]

        fields_mapping = ", ".join(f"{field} = :{field}" for field in field_names)
        pk_mapping = " AND ".join(f"{field} = :{field}" for field in pk)

        return f"UPDATE {table_name} SET {fields_mapping} WHERE {pk_mapping}"

    def update(self, *entries: T) -> None:
        if len(entries) == 1 and isinstance(entries[0], list):
            entries = entries[0]

        grouped_entries: Dict[Type[T], List[T]] = group_by(lambda e: type(e), entries)

        for cls, entries in grouped_entries.items():
            table_name = cls.type()

            pk = self.__pk(table_name)

            def get_pk(entry):
                return tuple(getattr(entry, f) for f in pk)

            existing_entries = self.get_entries(cls)

            pk_mapping = {get_pk(entry): entry for entry in existing_entries}

            entries_to_update = []
            entries_to_insert = []

            for entry in entries:
                existing_entry = pk_mapping.get(get_pk(entry))

                if not existing_entry:
                    entries_to_insert.append(entry)
                elif existing_entry != entry:
                    entries_to_update.append((entry, existing_entry))

            if entries_to_insert:
                dicts_to_insert = [entry.as_dict() for entry in entries_to_insert]

                # for field_to_insert, dicts in group_by(lambda e: tuple(e.keys()), dicts_to_insert).items():
                insert_query = self.__insert_query(cls)

                self.__db.executemany(
                    insert_query,
                    dicts_to_insert
                )

                self.__drop_cache(cls)

            if entries_to_update:
                fieldsets_grouping = defaultdict(lambda: [])

                for entry, existing_entry in entries_to_update:
                    diff = entry.diff(existing_entry)
                    fields_to_update = diff.keys()
                    fields_to_update = tuple(fields_to_update)

                    fieldsets_grouping[fields_to_update].append(entry.as_dict())

                for fields_to_update, dicts_to_update in fieldsets_grouping.items():
                    update_query = self.__update_query(cls, fields_to_update)

                    self.__db.executemany(
                        update_query,
                        dicts_to_update
                    )

                self.__drop_cache(cls)

    def delete(self, *entries: T) -> None:
        if len(entries) == 1 and isinstance(entries[0], list):
            entries = entries[0]

        grouped_entries: Dict[Type[T], List[T]] = group_by(lambda e: type(e), entries)

        for cls, entries in grouped_entries.items():
            table_name = cls.type()

            pk = self.__pk(table_name)

            pk_mapping = " AND ".join(f"{field} = :{field}" for field in pk)

            delete_query = f"DELETE FROM {table_name} WHERE {pk_mapping}"
            dicts_to_delete = [entry.as_dict() for entry in entries]

            self.__db.executemany(
                delete_query,
                dicts_to_delete
            )

            self.__drop_cache(cls)
