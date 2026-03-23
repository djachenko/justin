import time
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

import click
from lazy_object_proxy import Proxy
from pyvko.config.config import Config as PyvkoConfig
from pyvko.pyvko_main import Pyvko
from typer import Typer, Context, Argument
from typer.core import TyperGroup

from justin.cms.cms import CMS
from justin.cms_2.sqlite_cms import SQLiteCMS
from justin.cms_2.storage.google_sheets.google_sheets_database import GoogleSheetsDatabase
from justin.di.app import DI
from justin.di.metafiles import setup_metafiles
from justin.shared.config import Config
from justin.shared.context import Context as JustinContext
from justin.shared.models.photoset_migration import PhotosetMigrationFactory
from justin.shared.world import World
from justin.typer.app.tracker import write_entry, TrackEntry, setup_tracking
from justin.typer.attach_album_command import app as attach_album_app
from justin.typer.check_ratios_command import app as check_ratios_app
from justin.typer.date_split_command import app as date_split_app
from justin.typer.delete_posts_command import app as delete_posts_app
from justin.typer.drone_command import app as drone_app
from justin.typer.fix_metafile_command import app as fix_metafile_app
from justin.typer.json2sqlite_command import app as json2sqlite_app
from justin.typer.manage_tags_command import app as manage_tags_app
from justin.typer.populate_command import app as populate_app
from justin.typer.register_people_command import app as register_people_app
from justin.typer.sequence_command import app as sequence_app
from justin.typer.setup_event_command import app as setup_event_app
from justin.typer.split_command import app as split_app
from justin.typer.stage_command import create_stage_commands
from justin.typer.step_sources_command import app as step_sources_app
from justin.typer.web_sync_command import app as web_sync_app
from justin.typer.upload_command import app as upload_app

__CONFIGS_FOLDER = ".justin"
__CONFIG_FILE = "config.py"
__PYVKO_CONFIG_FILE = "pyvko_config.json"
__CMS_FOLDER = "cms"
__GOOGLE_SHEETS_FOLDER = "google_sheets"

setup_metafiles()


class TrackedGroup(TyperGroup):
    def invoke(self, ctx: click.Context) -> Any:
        print("tracking started")

        start = time.perf_counter()
        error: str | None = None
        command_name = " ".join(ctx.protected_args + ctx.args)

        try:
            return super().invoke(ctx)
        except Exception as e:
            error = type(e).__name__ + ": " + str(e)
            raise
        finally:
            elapsed = time.perf_counter() - start

            write_entry(TrackEntry(
                command=command_name or "unknown",
                timestamp=datetime.now().isoformat(),
                duration=elapsed,
                error=error,
            ))


def build_app(config_path: Path) -> Typer:
    configs_folder = config_path / __CONFIGS_FOLDER
    pyvko_config_file = configs_folder / __PYVKO_CONFIG_FILE
    cms_root = configs_folder / __CMS_FOLDER
    google_sheets_root = configs_folder / __GOOGLE_SHEETS_FOLDER

    setup_tracking(configs_folder)

    pyvko_config = PyvkoConfig.read(pyvko_config_file)
    pyvko = Pyvko(pyvko_config)
    cms = CMS(cms_root)
    sqlite_cms = SQLiteCMS(cms_root)

    sheets_db = GoogleSheetsDatabase(
        spreadsheet_id="1wpjgMa8PIsi7uVzkVG9G1Q_kP_lOnCgbBLKzZYssKzc",
        root=google_sheets_root
    )

    config = Config.from_source(configs_folder / __CONFIG_FILE, init_globals={
        "NAMES": sqlite_cms.get_all_folders(),
    })

    di = DI(config)

    def get_lazy_group(url_key):
        return Proxy(lambda: pyvko.get_by_url(config[url_key]))

    justin_context = JustinContext(
        world=Proxy(lambda: World()),
        justin_group=get_lazy_group(Config.Keys.JUSTIN_URL),
        closed_group=get_lazy_group(Config.Keys.CLOSED_URL),
        meeting_group=get_lazy_group(Config.Keys.MEETING_URL),
        kot_i_kit_group=get_lazy_group(Config.Keys.KOT_I_KIT_URL),
        my_people_group=get_lazy_group(Config.Keys.MY_PEOPLE_URL),
        cullen_group=get_lazy_group(Config.Keys.CULLEN_URL),
        pyvko=pyvko,
        cms=cms,
        aftershoot_stats=cms_root / "aftershoot.json",
        drive_path=Path.home() / "Yandex.Disk.localized" / "photos",
        sqlite_cms=sqlite_cms,
        sheets_db=sheets_db,
        photoset_migrations_factory=PhotosetMigrationFactory(cms)
    )

    app = Typer(cls=TrackedGroup)

    subapps = [
        # attach_album_app,
        # date_split_app,
        # delete_posts_app,
        # drone_app,
        # check_ratios_app,
        # fix_metafile_app,
        # json2sqlite_app,
        # manage_tags_app,
        # populate_app,
        # register_people_app,
        # sequence_app,
        # setup_event_app,
        # split_app,
        # step_sources_app,
        upload_app,
        # web_sync_app,
    ]

    for subapp in subapps:
        app.add_typer(subapp)

    app.add_typer(create_stage_commands(di))

    @app.callback()
    def setup(context: Annotated[Context, Argument()]) -> None:
        context.obj = justin_context

    return app
