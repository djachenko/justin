import dataclasses
import json
from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Dict, Type, TypeVar, List, Set, Self
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
    __METAFILE_NAME = "_meta.json"
    TYPE_KEY = "type"

    @classmethod
    @cache
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

    @classmethod
    def metafile_path(cls, folder: Folder) -> Path:
        return folder.path / RootMetafile.__METAFILE_NAME

    @classmethod
    @cache
    def __reader(cls) -> 'MetafileReadWriter':
        return MetafileReadWriter.instance()

    @classmethod
    def has(cls, folder: Folder) -> bool:
        if not cls.metafile_path(folder).exists():
            return False

        # if metafile_type is None:
        #     return True

        return cls.get(folder) is not None

    @classmethod
    def get(cls, folder: Folder) -> Self | None:
        if not cls.metafile_path(folder).exists():
            return None

        return cls.__reader().read(cls.metafile_path(folder), cls)

    def save(self, folder: Folder) -> None:
        self.__reader().write(self, self.metafile_path(folder))

    @classmethod
    def remove(cls, folder: Folder) -> None:
        metafile_path = cls.metafile_path(folder)

        if cls == RootMetafile:
            assert False

            metafile_path.unlink(missing_ok=True)

            return

        metafiles: List[RootMetafile] = cls.__reader().read_all(metafile_path)

        saved_metafiles = [metafile for metafile in metafiles if type(metafile) is cls]

        metafile_path.unlink(missing_ok=True)

        for metafile in saved_metafiles:
            metafile.save(folder)

    @classmethod
    def collect_metafile_paths(cls, folder: Folder) -> List[Path]:
        return [cls.metafile_path(folder)] + \
            util.flat_map(cls.collect_metafile_paths(subfolder) for subfolder in folder.subfolders)


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
