import dataclasses
from enum import Flag, auto
from typing import Iterable, Tuple, Any, List, Type, TypeVar, Dict

from justin.actions.named.stage.exceptions.no_files_for_name_error import NoFilesForNameError


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
    CLOSED = auto()
    PHOTOCLUB = auto()
    SIGNED = JUSTIN | MY_PEOPLE | CLOSED | PHOTOCLUB | MEETING | KOT_I_KIT
    ALL = SELECTION | SIGNED


V = TypeVar('V')
Json = Dict[str, 'Json'] | List['Json'] | str


def fromdict(obj: Json, data_class: Type[V]) -> V:
    fields = dataclasses.fields(data_class)

    dict_ = {}

    for field in fields:
        try:
            dict_[field.name] = field.type(obj[field.name])
        except TypeError:
            dict_[field.name] = None

    new_instance = data_class(**dict_)

    return new_instance


def first_e(seq: Iterable[V]) -> V | None:
    i = None

    for i in seq:
        break

    return i
