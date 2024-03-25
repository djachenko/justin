from abc import ABC
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Type, List
from uuid import UUID

from justin.cms.base_cms import Entry, T, Table, BaseCMS
from justin.shared.helpers.utils import Json
from justin.shared.metafile import MetaFolder, PhotosetMetafile
from justin.shared.models.photoset import Photoset
from justin.shared.world import Location, World


@dataclass
class PhotosetEntry(Entry):
    photoset_id: UUID
    name: str
    size: int
    location: str
    people: List[str]

    @classmethod
    def from_dict(cls: Type[T], json_object: Json) -> T:
        entry = super().from_dict(json_object)

        entry.location = Location(MetaFolder(Path(json_object["location"])))
        entry.people = json_object["people"]

        return entry

    def as_dict(self) -> Json:
        json_object = super().as_dict()

        json_object["photoset_id"] = self.photoset_id.hex

        return json_object


class PhotosetsCMS(BaseCMS, ABC):
    @property
    @lru_cache()
    def photosets(self) -> Table[PhotosetEntry, UUID]:
        return Table(self.root / "photosets.json", PhotosetEntry, lambda x: x.photoset_id)

    def index_folder(self, folder: MetaFolder, world: World) -> None:
        roots = [folder]

        while roots:
            candidate = roots.pop(0)

            if candidate.has_metafile(PhotosetMetafile):
                self.index_photoset(Photoset.from_folder(candidate), world)
            else:
                roots += candidate.subfolders

    def index_photoset(self, photoset: Photoset, world: World) -> None:
        assert photoset.folder.has_metafile(PhotosetMetafile)

        metafile = photoset.folder.get_metafile(PhotosetMetafile)

        people = []

        if photoset.my_people:
            people += photoset.my_people.subfolders

        if photoset.closed:
            people += photoset.closed.subfolders

        if photoset.drive:
            people += photoset.drive.subfolders

        people = [person.name for person in people]

        photoset_entry = PhotosetEntry(
            photoset_id=metafile.photoset_id,
            name=photoset.name,
            size=photoset.folder.total_size,
            location=world.location_of_path(photoset.path).name,
            people=people
        )

        self.photosets.update(photoset_entry)
        self.photosets.save()
