import dataclasses
import json
from abc import abstractmethod, ABC
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Dict, Type, TypeVar, List, Set
from uuid import UUID, uuid4

from justin.shared.filesystem import Folder
from justin.shared.helpers.utils import Json, fromdict
from justin_utils import util
from justin_utils.singleton import Singleton

T = TypeVar('T', bound='Metafile')
V = TypeVar('V', bound='RootMetafile')


# region metafile classes

class Metafile:

    @classmethod
    @abstractmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        pass

    @abstractmethod
    def as_json(self) -> Json:
        # todo: asdict(self)
        return {}


@dataclass
class RootMetafile(Metafile):
    TYPE_KEY = "type"

    @classmethod
    @lru_cache()
    @abstractmethod
    def type(cls) -> str:
        pass

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        return fromdict(json_object, cls)

    def as_json(self) -> Json:
        return super().as_json() | {
            RootMetafile.TYPE_KEY: self.type()
        } | asdict(self)


class PostStatus(Metafile, Enum):
    SCHEDULED = "scheduled"
    PUBLISHED = "published"

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        assert isinstance(json_object, str)

        return cls(json_object)

    def as_json(self) -> Json:
        return str(self.value)


DATE_FORMAT_D_M_Y = "%d.%m.%y"


@dataclass
class PhotosetMetafile(RootMetafile):
    photoset_id: UUID = field(default_factory=lambda: uuid4())

    @classmethod
    def type(cls) -> str:
        return "photoset"

    def as_json(self) -> Json:
        return super().as_json() | {
            "photoset_id": self.photoset_id.hex
        }


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
class NoPostMetafile(RootMetafile):
    @classmethod
    def type(cls) -> str:
        return "no_post"


@dataclass
class GroupMetafile(RootMetafile):
    group_id: int

    @classmethod
    def type(cls) -> str:
        return "group"


@dataclass
class CommentMetafile(Metafile):
    id: int
    files: List[str]
    status: PostStatus

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        return CommentMetafile(
            id=json_object["id"],
            files=json_object["files"],
            status=PostStatus.from_json(json_object["status"]),
        )

    def as_json(self) -> Json:
        self_as_dict = asdict(self)

        self_as_dict["status"] = self.status.as_json()

        return super().as_json() | self_as_dict


@dataclass
class PersonMetafile(RootMetafile):
    comments: List[CommentMetafile] = field(default_factory=lambda: [])

    @classmethod
    def type(cls) -> str:
        return "person"

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        return PersonMetafile(
            comments=[CommentMetafile.from_json(comment) for comment in json_object["comments"]],
        )

    def as_json(self) -> Json:
        return super().as_json() | {
            "comments": [comment.as_json() for comment in self.comments]
        }


@dataclass
class AlbumMetafile(RootMetafile):
    album_id: int
    images: List[str]

    @classmethod
    def type(cls) -> str:
        return "album"

    def as_json(self) -> Json:
        return super().as_json() | asdict(self)

    @classmethod
    def from_json(cls: Type[T], json_object: Json) -> T:
        return AlbumMetafile(
            album_id=json_object["album_id"],
            images=json_object["images"]
        )


@dataclass
class LocationMetafile(RootMetafile):
    location_name: str
    location_description: str
    location_order: int

    @classmethod
    def type(cls) -> str:
        return "location"


# endregion metafile classes


# region metafile migrations


class MetafileMigration(Singleton):
    @property
    @abstractmethod
    def supported_types(self) -> List[str]:
        pass

    @abstractmethod
    def migrate(self, json_object: Json) -> Json:
        pass

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __hash__(self):
        return hash(self.__class__)


class NegativeGroupIdMigration(MetafileMigration):
    @property
    def supported_types(self) -> List[str]:
        return [
            GroupMetafile.type(),
        ]

    def migrate(self, json_dict: Json) -> Json:
        json_dict = json_dict.copy()

        json_dict["group_id"] = -abs(json_dict["group_id"])

        return json_dict


class MetafileMigrator(Singleton):
    def __init__(self) -> None:
        super().__init__()

        self.__migrations: Dict[str, Set[MetafileMigration]] = defaultdict(set)

    def register(self, *migrations: MetafileMigration) -> None:
        for migration in migrations:
            for supported_type in migration.supported_types:
                migrations_for_type = self.__migrations[supported_type]

                assert migration not in migrations_for_type

                migrations_for_type.add(migration)

    def migrate(self, json_dict: Json) -> Json:
        for json_type in json_dict[RootMetafile.TYPE_KEY]:
            for migration in self.__migrations[json_type]:
                json_dict = migration.migrate(json_dict)

        return json_dict

    def migrate_path(self, path: Path) -> None:
        if not path.exists() or path.stat().st_size <= 0:
            return

        with path.open() as metafile_file:
            json_dict = json.load(metafile_file)

        if RootMetafile.TYPE_KEY not in json_dict:
            return

        migrated = self.migrate(json_dict)

        with path.open(mode="w") as metafile_file:
            json.dump(migrated, metafile_file, indent=4)


MetafileMigrator.instance().register(
    NegativeGroupIdMigration.instance(),
)


# endregion metafile migrations

# region metafile reading


class MetafileReadWriter(Singleton):
    def __init__(self) -> None:
        super().__init__()

        self.__mapping: Dict[str, Type[RootMetafile]] = {}
        self.__migrator = MetafileMigrator.instance()

    def register(self, *types: Type[RootMetafile]) -> None:
        fields = []

        for type_ in types:
            fields += dataclasses.fields(type_)

            assert type_.type() not in self.__mapping

            self.__mapping[type_.type()] = type_

        assert len(set(fields)) == len(fields)

    def read(self, path: Path, metafile_type: V = None) -> V | None:
        metafiles = self.read_all(path)

        if len(metafiles) == 0:
            return None

        if len(metafiles) == 1 and metafile_type is None:
            return metafiles[0]

        for metafile in metafiles:
            if type(metafile) == metafile_type:
                return metafile

        return None

    def read_all(self, path: Path) -> List[V]:
        self.__migrator.migrate_path(path)

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
    PersonMetafile,
    PhotosetMetafile,
    AlbumMetafile,
    LocationMetafile,
    NoPostMetafile,
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

    def has_metafile(self, metafile_type: Type[V] = None) -> bool:
        if not self.metafile_path.exists():
            return False

        if metafile_type is None:
            return True

        return self.get_metafile(metafile_type) is not None

    def get_metafile(self, metafile_type: Type[V] = None) -> V | None:
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


class MetaFolder(Folder, MetafileMixin):
    @property
    def subfolders(self) -> List['MetaFolder']:
        # noinspection PyTypeChecker
        return super().subfolders

    def collect_metafile_paths(self) -> List[Path]:
        return super().collect_metafile_paths() + \
            util.flat_map(subtree.collect_metafile_paths() for subtree in self.subfolders)

# endregion metafile mixins
