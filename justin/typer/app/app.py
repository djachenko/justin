from pathlib import Path
from typing import Annotated

from lazy_object_proxy import Proxy
from typer import Typer, Context, Argument

from justin.cms.cms import CMS
from justin.cms_2.sqlite_cms import SQLiteCMS
from justin.cms_2.storage.google_sheets.google_sheets_database import GoogleSheetsDatabase
from justin.di.app import DI
from justin.di.metafiles import setup_metafiles
from justin.shared.config import Config
from justin.shared.context import Context as JustinContext
from justin.shared.models.photoset_migration import PhotosetMigrationFactory
from justin.shared.world import World
from justin.typer.app.tracker import Tracker
from justin.typer.date_split_command import app as date_split_app
from justin.typer.register_people_command import app as register_people_app
from justin.typer.sequence_command import app as sequence_app
from justin.typer.stage_command.stage_command import create_stage_commands
from justin.typer.upload_command import app as upload_app
from pyvko.config.config import Config as PyvkoConfig
from pyvko.pyvko_main import Pyvko

__CONFIGS_FOLDER = ".justin"
__CONFIG_FILE = "config.py"
__PYVKO_CONFIG_FILE = "pyvko_config.json"
__CMS_FOLDER = "cms"
__GOOGLE_SHEETS_FOLDER = "google_sheets"

setup_metafiles()


def build_app(config_path: Path) -> Typer:
    configs_folder = config_path / __CONFIGS_FOLDER
    pyvko_config_file = configs_folder / __PYVKO_CONFIG_FILE
    cms_root = configs_folder / __CMS_FOLDER
    google_sheets_root = configs_folder / __GOOGLE_SHEETS_FOLDER

    Tracker.instance().setup(configs_folder)

    pyvko_config = PyvkoConfig.read(pyvko_config_file)
    pyvko = Pyvko(pyvko_config)
    cms = CMS(cms_root)
    sqlite_cms = SQLiteCMS(cms_root)

    sheets_db = GoogleSheetsDatabase(
        spreadsheet_id="1wpjgMa8PIsi7uVzkVG9G1Q_kP_lOnCgbBLKzZYssKzc",
        root=google_sheets_root
    )

    config = Config.from_source(configs_folder / __CONFIG_FILE, init_globals={
        "names": sqlite_cms.get_all_folders(),
    })

    di = DI(config)

    def get_lazy_group(url):
        return Proxy(lambda: pyvko.get_by_url(url))

    yandex_disk_path = Path.home() / "Yandex.Disk.localized"

    drive_path = yandex_disk_path / "photos"
    cullen_path = yandex_disk_path / "cullen"

    justin_context = JustinContext(
        world=Proxy(lambda: World()),
        justin_group=get_lazy_group(config.justin_url),
        closed_group=get_lazy_group(config.closed_url),
        meeting_group=get_lazy_group(config.meeting_url),
        kot_i_kit_group=get_lazy_group(config.kot_i_kit_url),
        my_people_group=get_lazy_group(config.my_people_url),
        cullen_group=get_lazy_group(config.cullen_url),
        pyvko=pyvko,
        cms=cms,
        aftershoot_stats=cms_root / "aftershoot.json",
        drive_path=drive_path,
        cullen_path=cullen_path,
        sqlite_cms=sqlite_cms,
        sheets_db=sheets_db,
        photoset_migrations_factory=PhotosetMigrationFactory(cms)
    )

    app = Typer()

    subapps = [
        date_split_app,
        sequence_app,
        upload_app,
        register_people_app,
    ]

    for subapp in subapps:
        app.add_typer(subapp)

    app.add_typer(create_stage_commands(di.stages_factory))

    @app.callback()
    def setup(context: Annotated[Context, Argument()]) -> None:
        context.obj = justin_context

    return app
