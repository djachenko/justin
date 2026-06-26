from pathlib import Path

from justin_utils.cd import cd

from justin.typer.app.app import build_app
from justin.typer.app.ide_runner_local import get_config
from justin.typer.app.ide_runner_types import Commands, Locations, RunConfig, Stages
from justin.typer.app.tracker import track



def _default_config() -> RunConfig:
    return RunConfig(
        cwd=Path(f"{Locations.MAC_OS_HOME.value}photos/stages/{Stages.FILTER.value}"),
        command=Commands.READY.value,
    )


def main() -> None:
    try:
        cfg = get_config()
    except ImportError:
        cfg = _default_config()

    app = build_app(Path.home())

    with cd(cfg.cwd):
        with track():
            app(cfg.command.split())


if __name__ == '__main__':
    main()
