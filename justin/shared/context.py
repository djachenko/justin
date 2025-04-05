from dataclasses import dataclass

from justin.cms.cms import CMS
from justin.cms.google_sheets_database import GoogleSheetsDatabase
from justin.cms_2.sqlite_cms import SQLiteCMS
from justin.shared.models.photoset_migration import PhotosetMigrationFactory
from justin.shared.world import World
from pyvko.aspects.groups import Group
from pyvko.aspects.posts import Posts
from pyvko.pyvko_main import Pyvko


@dataclass(frozen=True)
class Context:
    world: World
    justin_group: Group
    closed_group: Group
    meeting_group: Group
    kot_i_kit_group: Group
    my_people_group: Posts

    pyvko: Pyvko

    cms: CMS
    sqlite_cms: SQLiteCMS

    sheets_db: GoogleSheetsDatabase

    photoset_migrations_factory: PhotosetMigrationFactory

    @property
    def default_group(self) -> Group:
        return self.justin_group
