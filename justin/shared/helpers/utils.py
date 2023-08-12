from abc import abstractmethod
from dataclasses import dataclass, asdict, fields
from enum import Flag, auto
from typing import Iterable, Tuple, Any, List, Type, TypeVar, Dict

from justin.actions.stage.exceptions.no_files_for_name_error import NoFilesForNameError


def __validate_join(join: Iterable[Tuple[str, Any]], name: str):
    names_of_unjoined_files = []

    for source_name, source in join:
        if source is None:
            names_of_unjoined_files.append(source_name)

    if names_of_unjoined_files:
        unjoined_files_names_string = ", ".join(names_of_unjoined_files)

        raise NoFilesForNameError(f"Failed join for {name}: {unjoined_files_names_string}")


class JpegType(Flag):
    SELECTION = auto()
    JUSTIN = auto()
    MEETING = auto()
    KOT_I_KIT = auto()
    MY_PEOPLE = auto()
    DRIVE = auto()
    CLOSED = auto()
    PHOTOCLUB = auto()
    SIGNED = JUSTIN | MY_PEOPLE | CLOSED | PHOTOCLUB | MEETING | KOT_I_KIT | DRIVE
    ALL = SELECTION | SIGNED


V = TypeVar('V')
Json = Dict[str, 'Json'] | List['Json'] | str


class JsonSerializable:
    @classmethod
    @abstractmethod
    def from_json(cls: Type[V], json_object: Json) -> V:
        pass

    @abstractmethod
    def as_json(self) -> Json:
        pass


@dataclass
class JsonDataclass(JsonSerializable):
    @classmethod
    def from_json(cls: Type[V], json_object: Json) -> V:
        return fromdict(json_object, cls)

    def as_json(self) -> Json:
        return asdict(self)


def fromdict(obj: Json, data_class: Type[V]) -> V:
    fields_ = fields(data_class)

    dict_ = {}

    for field in fields_:
        field_name = field.name
        try:
            if field_name in obj:
                if issubclass(field.type, JsonSerializable):
                    dict_[field_name] = field.type.from_json(obj[field_name])
                else:
                    dict_[field_name] = field.type(obj[field_name])
            else:
                dict_[field_name] = field.default
        except (TypeError, ValueError):
            dict_[field_name] = None

    new_instance = data_class(**dict_)

    return new_instance


def first_e(seq: Iterable[V]) -> V | None:
    i = None

    for i in seq:
        break

    return i
