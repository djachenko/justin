from abc import abstractmethod

from justin.cms_2.storage.sqlite.sqlite_database import SQLiteDatabase
from justin.cms_2.storage.sqlite.sqlite_entries import SyncedTagsPost


class SyncedTagsCMS:
    @property
    @abstractmethod
    def db(self) -> SQLiteDatabase:
        pass

    def is_synced(self, post_id: int, group_id: int) -> bool:
        with self.db.connect():
            existing_entries = self.db.get_entries(SyncedTagsPost)

        return any(entry.post_id == post_id and entry.group_id == group_id for entry in existing_entries)

    def mark_synced(self, post_id: int, group_id: int) -> None:
        with self.db.connect():
            self.db.update(SyncedTagsPost(post_id, group_id))
