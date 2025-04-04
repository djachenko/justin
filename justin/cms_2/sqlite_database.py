import sqlite3
from abc import ABC
from contextlib import contextmanager
from dataclasses import dataclass, fields, asdict
from functools import cache
from pathlib import Path
from sqlite3 import Cursor, Row, Connection
from typing import TypeVar, List, Type, Self, Iterable, Any, Dict

from justin.shared.helpers.utils import fromdict
from justin_utils.util import group_by
from pyvko.shared.utils import Json


@dataclass
class SQLiteEntry(ABC):
    @classmethod
    def type(cls) -> str:
        return cls.__name__

    @classmethod
    def from_dict(cls, json_object: Json) -> Self:
        return cls(**json_object)
        # return fromdict(json_object, cls)

    @classmethod
    def from_cursor(cls, cursor: Cursor, row) -> Self:
        object_mapping = dict(zip([d[0] for d in cursor.description], row))

        # noinspection PyArgumentList
        return cls(**object_mapping)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


T = TypeVar("T", bound=SQLiteEntry)


class DBLogger:
    def commit(self) -> None:
        pass

    def close(self) -> None:
        pass

    def execute(self, query: str) -> None:
        print(query)

    def executemany(self, query: str, entries: Iterable[Dict[str, Any]]) -> None:
        pass


class SQLiteDatabase:
    def __init__(self, root: Path, file_name: str = "justin.db") -> None:
        self.__db_path = root / file_name
        self.__db: Connection | None = None

    @contextmanager
    def connect(self) -> None:
        self.__db = sqlite3.connect(self.__db_path)

        yield

        self.__db.commit()
        self.__db.close()

        self.__db = None

    def get_entries(self, cls: Type[T]) -> List[T]:
        query = f"SELECT * FROM {cls.type()}"

        cursor = self.__db.execute(query)
        fieldnames = tuple(d[0] for d in cursor.description)

        def row_factory(_, row):
            row_dict = dict(zip(fieldnames, row))

            # return cls(**row_dict)
            return cls.from_dict(row_dict)

        cursor.row_factory = row_factory

        return cursor.fetchall()

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
    def __insert_query(self, cls: Type[T], key_mask: Iterable[str] | None = None) -> str:
        table_name = cls.type()
        fields_ = fields(cls)

        field_names = [field.name for field in fields_]

        if key_mask:
            field_names = [name for name in field_names if name in key_mask]

        columns = ", ".join(field_names)
        parameters = ", ".join(f":{name}" for name in field_names)

        return f"INSERT INTO {table_name} ({columns}) VALUES({parameters})"

    @cache
    def __update_query(self, cls: Type[T], key_mask: Iterable[str] | None = None) -> str:
        table_name = cls.type()
        fields_ = fields(cls)

        pk = self.__pk(table_name)

        field_names = [field.name for field in fields_]

        if key_mask:
            assert not any(key in key_mask for key in pk)

            field_names = [name for name in field_names if name in key_mask]

        fields_mapping = ", ".join(f"{field} = :{field}" for field in field_names)
        pk_mapping = ", ".join(f"{field} = :{field}" for field in pk)

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
                    entries_to_update.append(entry)

            dicts_to_insert = [entry.as_dict() for entry in entries_to_insert]

            for key_set, entries in group_by(lambda e: tuple(e.keys()), dicts_to_insert).items():
                insert_query = self.__insert_query(cls, key_set)

                self.__db.executemany(
                    insert_query,
                    entries
                )

            dicts_to_update = [entry.as_dict() for entry in entries_to_update]

            for key_set, entries in group_by(lambda e: tuple(e.keys()), dicts_to_update).items():
                update_query = self.__update_query(cls, key_set)

                self.__db.executemany(
                    update_query,
                    entries
                )

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
