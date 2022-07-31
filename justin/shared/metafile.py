import dataclasses
import json
from abc import abstractmethod, ABC
from dataclasses import dataclass, asdict
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, Type, TypeVar, List

from justin_utils.singleton import Singleton

T = TypeVar('T', bound='RootMetafile')

Json = Dict[str, 'Json'] | List['Json'] | str


# region metafile classes

class Metafile:

    @classmethod
    @abstractmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        pass

    @abstractmethod
    def as_json(self) -> Json:
        return {}


@dataclass
class RootMetafile(Metafile):
    TYPE_KEY = "type"

    @classmethod
    @lru_cache()
    @abstractmethod
    def type(cls) -> str:
        pass

    def as_json(self) -> Json:
        return super().as_json() | {
            RootMetafile.TYPE_KEY: self.type()
        }


class PostStatus(Metafile, Enum):
    SCHEDULED = "scheduled"
    PUBLISHED = "published"

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        assert isinstance(json_object, str)

        return cls(json_object)

    def as_json(self) -> Json:
        return self.value


@dataclass
class PostMetafile(RootMetafile):
    post_id: int
    status: PostStatus

    @classmethod
    def type(cls) -> str:
        return "post"

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        return PostMetafile(
            post_id=json_object["post_id"],
            status=PostStatus.from_json(json_object["status"])
        )

    def as_json(self) -> Json:
        self_as_dict = asdict(self)

        self_as_dict["status"] = self.status.as_json()

        return super().as_json() | self_as_dict


@dataclass
class GroupMetafile(RootMetafile):
    group_id: int

    @classmethod
    def type(cls) -> str:
        return "group"

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        return GroupMetafile(
            group_id=json_object["group_id"]
        )

    def as_json(self) -> Json:
        return super().as_json() | asdict(self)


# endregion metafile classes


# region metafile reading

class MetafileReadWriter(Singleton):
    def __init__(self) -> None:
        super().__init__()

        self.__mapping: Dict[str, Type[RootMetafile]] = {}

    def register(self, *types: Type[RootMetafile]) -> None:
        fields = []

        for type_ in types:
            fields += dataclasses.fields(type_)

        assert len(set(fields)) == len(fields)

        self.__mapping |= {type_.type(): type_ for type_ in types}

    def read(self, path: Path, metafile_type: T = None) -> Optional[T]:
        metafiles = self.read_all(path)

        if len(metafiles) == 0:
            return None

        if len(metafiles) == 1 and metafile_type is None:
            return metafiles[0]

        for metafile in metafiles:
            if type(metafile) == metafile_type:
                return metafile

        return None

    def read_all(self, path: Path) -> List[T]:
        if not path.exists() or path.stat().st_size <= 0:
            return []

        with path.open() as metafile_file:
            json_dict = json.load(metafile_file)

        if RootMetafile.TYPE_KEY not in json_dict:
            return []

        metafile_types = json_dict[RootMetafile.TYPE_KEY]

        metafiles = []

        for metafile_type in metafile_types:
            assert metafile_type in self.__mapping

            parser = self.__mapping[metafile_type]

            metafile = parser.from_json(json_dict)

            metafiles.append(metafile)

        return metafiles

    # noinspection PyMethodMayBeStatic
    def write(self, metafile: RootMetafile, path: Path) -> None:
        if path.exists():
            with path.open() as metafile_file:
                old_json = json.load(metafile_file)
        else:
            old_json = {
                RootMetafile.TYPE_KEY: []
            }

        new_json = metafile.as_json()

        # assert set(old_json.keys()).intersection(new_json.keys()) == {"type", }

        result_json = old_json | new_json

        result_json[RootMetafile.TYPE_KEY] = list(set(
            old_json[RootMetafile.TYPE_KEY] + [new_json[RootMetafile.TYPE_KEY]]
        ))

        with path.open(mode="w") as metafile_file:
            json.dump(result_json, metafile_file, indent=4)


MetafileReadWriter.instance().register(
    PostMetafile,
    GroupMetafile,
)


# endregion metafile reading


# region metafile mixins

class MetafileMixin(ABC):
    __METAFILE_NAME = "_meta.json"

    # noinspection PyTypeChecker
    @property
    @abstractmethod
    def path(self) -> Path:
        assert False

    @property
    def metafile_path(self) -> Path:
        return self.path / MetafileMixin.__METAFILE_NAME

    @property
    @lru_cache()
    def __reader(self):
        return MetafileReadWriter.instance()

    def has_metafile(self, metafile_type: Type[T] = None) -> bool:
        if not self.metafile_path.exists():
            return False

        if metafile_type is None:
            return True

        return self.get_metafile(metafile_type) is not None

    def get_metafile(self, metafile_type: Type[T] = None) -> T | None:
        if not self.metafile_path.exists():
            return None

        return self.__reader.read(self.metafile_path, metafile_type)

    def save_metafile(self, metafile: RootMetafile):
        self.__reader.write(metafile, self.metafile_path)

    def remove_metafile(self, metafile_type: Type[RootMetafile] = None):
        if metafile_type is None:
            self.metafile_path.unlink(missing_ok=True)

            return

        metafiles = self.__reader.read_all(self.metafile_path)

        saved_metafiles = [metafile for metafile in metafiles if type(metafile) != metafile_type]

        self.metafile_path.unlink(missing_ok=True)

        for metafile in saved_metafiles:
            self.save_metafile(metafile)

    def collect_metafile_paths(self) -> List[Path]:
        return [self.metafile_path]

# endregion metafile mixins
