from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, asdict, fields
from enum import Flag, auto
from types import UnionType, NoneType
from typing import Iterable, Tuple, Any, List, Type, TypeVar, Dict, get_origin, get_args

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


def fromdict(obj: Json, data_class: Type[V], rules: Dict[type, Callable] = None) -> V:
    rules = rules or {}

    fields_ = fields(data_class)

    dict_ = {}

    for field in fields_:
        field_name = field.name
        field_type = field.type

        origin = get_origin(field_type)

        if origin == UnionType:
            args = get_args(field_type)

            args = tuple(arg for arg in args if arg != NoneType)

            assert len(args) == 1

            field_type = args[0]

        new_value = None

        try:
            if field_name in obj:
                json_value = obj[field_name]

                if field_type in rules:
                    new_value = rules[field_type](json_value)
                elif issubclass(field_type, JsonSerializable):
                    new_value = field_type.from_json(json_value)
                else:
                    new_value = field_type(json_value)
            else:
                new_value = field.default
        except (TypeError, ValueError):
            new_value = None

        dict_[field_name] = new_value

    new_instance = data_class(**dict_)

    return new_instance


def first_e(seq: Iterable[V]) -> V | None:
    i = None

    for i in seq:
        break

    return i
