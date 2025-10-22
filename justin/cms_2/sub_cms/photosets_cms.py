from abc import abstractmethod
from typing import List, Type

from justin.cms_2.storage.sqlite.sqlite_database import SQLiteDatabase, SQLiteEntry
from justin.cms_2.storage.sqlite.sqlite_entries import Closed, Photoset as PhotosetEntry, PersonPhotos, Drive, MyPeople
from justin.shared.filesystem import Folder
from justin.shared.metafiles.metafile import PhotosetMetafile
from justin.shared.models.photoset import Photoset
from justin_utils.util import bfs


class PhotosetsCMS:
    @property
    @abstractmethod
    def db(self) -> SQLiteDatabase:
        pass

    def index_photoset(self, photoset: Photoset) -> None:
        assert PhotosetMetafile.has(photoset.folder)

        entries_to_index = [PhotosetEntry(
            folder=photoset.name
        )]

        def to_entries(folder: Folder | None, cls: Type[PersonPhotos]) -> List[SQLiteEntry]:
            if folder is None:
                return []

            # noinspection PyArgumentList
            return [cls(
                folder=subfolder.name,
                photoset=photoset.name,
                count=subfolder.file_count()
            ) for subfolder in folder.subfolders]

        entries_to_index += to_entries(photoset.drive, Drive)
        entries_to_index += to_entries(photoset.closed, Closed)
        entries_to_index += to_entries(photoset.my_people, MyPeople)

        with self.db.connect():
            self.db.update(*entries_to_index)

    def index_folder(self, folder: Folder) -> None:
        def provider(candidate: Folder) -> List[Folder]:
            if Photoset.is_photoset(candidate):
                self.index_photoset(Photoset.from_folder(candidate))

                return []
            else:
                return candidate.subfolders

        bfs(folder, provider)
