"""
Integration tests for ``TimelapseCommand``: a photoset folder in, a call to the generator out.

The command runs whole — photoset detection, parts, the timelapse destination.
The context is a mock without migrations, and the generator is mocked too: what
it builds is covered by ``test_timelapse_prproj``, here only what the command
asks it for matters.
"""

from pathlib import Path
from unittest.mock import Mock, patch

from justin.tools.timelapse.timelapse_settings import TimelapseSettings
from justin.typer.timelapse_command import TimelapseCommand
from tests.test_timelapse_prproj import make_timelapse

PHOTOSET = "26.05.31.testset"


def run_timelapse(root: Path, settings: TimelapseSettings = TimelapseSettings()) -> TimelapseSettings:
    context = Mock()
    context.photoset_migrations_factory.part_less_migrations.return_value = []
    context.photoset_migrations_factory.part_wise_migrations.return_value = []

    with patch("justin.typer.timelapse_command.generate_prproj") as generate_prproj:
        TimelapseCommand(context, [root / PHOTOSET], settings).run()

    generate_prproj.assert_called_once()

    _, passed = generate_prproj.call_args.args

    return passed


def test_single_sound_goes_on_timeline_by_default(tmp_path: Path) -> None:
    make_timelapse(tmp_path, photoset=PHOTOSET, sounds=("alpha.mp3",))

    assert run_timelapse(tmp_path).timeline_sounds == ["alpha.mp3"]


def test_several_sounds_stay_in_panel_by_default(tmp_path: Path) -> None:
    make_timelapse(tmp_path, photoset=PHOTOSET, sounds=("alpha.mp3", "beta.mp3"))

    assert run_timelapse(tmp_path).timeline_sounds == []


def test_explicit_timeline_sound_wins_over_default(tmp_path: Path) -> None:
    make_timelapse(tmp_path, photoset=PHOTOSET, sounds=("alpha.mp3",))
    settings = TimelapseSettings(timeline_sounds=["other"])

    assert run_timelapse(tmp_path, settings).timeline_sounds == ["other"]
