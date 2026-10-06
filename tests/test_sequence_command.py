from datetime import UTC, datetime, timedelta
from pathlib import Path

from justin_utils.exif import parse_exif
from justin_utils.filesystem import Folder
from PIL import Image
from PIL.ExifTags import IFD, Base

from justin.typer.sequence_command import SequenceCommand

BASE_DATE = datetime(2026, 9, 1, 12, tzinfo=UTC)


def make_photo(path: Path, date_taken: datetime) -> None:
    image = Image.new("RGB", (4, 4))
    exif = image.getexif()
    exif.get_ifd(IFD.Exif)[Base.DateTimeOriginal] = date_taken.strftime("%Y:%m:%d %H:%M:%S")
    image.save(path, exif=exif)


def make_series(folder: Path, count: int) -> None:
    for index in range(count):
        make_photo(folder / f"{index:04}.jpg", BASE_DATE + timedelta(seconds=index))


def run_sequence(folder: Path, start: int = 0, prefix: str | None = None) -> None:
    command = SequenceCommand.__new__(SequenceCommand)
    command._SequenceCommand__prefix = prefix  # type: ignore[attr-defined]
    command._SequenceCommand__start = start  # type: ignore[attr-defined]
    command.run_for_folder(Folder(folder), None)  # type: ignore[arg-type]


def seconds_by_name(folder: Path) -> dict[str, int]:
    result = {}

    for path in folder.iterdir():
        exif = parse_exif(path)
        assert exif is not None
        result[path.name] = int((exif.date_taken - BASE_DATE.replace(tzinfo=None)).total_seconds())

    return result


def test_numbers_from_zero_by_default(tmp_path: Path) -> None:
    make_photo(tmp_path / "a.jpg", BASE_DATE)
    make_photo(tmp_path / "b.jpg", BASE_DATE + timedelta(seconds=1))

    run_sequence(tmp_path)

    assert seconds_by_name(tmp_path) == {"0000.jpg": 0, "0001.jpg": 1}


def test_orders_by_exif_date_not_by_name(tmp_path: Path) -> None:
    make_photo(tmp_path / "a.jpg", BASE_DATE + timedelta(seconds=2))
    make_photo(tmp_path / "b.jpg", BASE_DATE + timedelta(seconds=1))
    make_photo(tmp_path / "c.jpg", BASE_DATE)

    run_sequence(tmp_path)

    assert seconds_by_name(tmp_path) == {"0000.jpg": 0, "0001.jpg": 1, "0002.jpg": 2}


def test_orders_by_name_without_exif(tmp_path: Path) -> None:
    for name in ("c", "a", "b"):
        (tmp_path / f"{name}.jpg").write_text(name)

    run_sequence(tmp_path)

    assert {path.name: path.read_text() for path in tmp_path.iterdir()} == {
        "0000.jpg": "a",
        "0001.jpg": "b",
        "0002.jpg": "c",
    }


def test_starts_from_given_number(tmp_path: Path) -> None:
    make_series(tmp_path, 2)

    run_sequence(tmp_path, start=5)

    assert seconds_by_name(tmp_path) == {"0005.jpg": 0, "0006.jpg": 1}


def test_applies_prefix(tmp_path: Path) -> None:
    make_series(tmp_path, 2)

    run_sequence(tmp_path, prefix="party")

    assert seconds_by_name(tmp_path) == {"party_0000.jpg": 0, "party_0001.jpg": 1}


def test_keeps_suffixes(tmp_path: Path) -> None:
    make_photo(tmp_path / "a.jpg", BASE_DATE)
    make_photo(tmp_path / "b.jpeg", BASE_DATE + timedelta(seconds=1))

    run_sequence(tmp_path)

    assert seconds_by_name(tmp_path) == {"0000.jpg": 0, "0001.jpeg": 1}


def test_rerun_with_same_arguments_changes_nothing(tmp_path: Path) -> None:
    make_series(tmp_path, 5)

    run_sequence(tmp_path)

    assert seconds_by_name(tmp_path) == {f"{index:04}.jpg": index for index in range(5)}


def test_renumbering_backward_closes_gap(tmp_path: Path) -> None:
    make_series(tmp_path, 10)
    (tmp_path / "0003.jpg").unlink()

    run_sequence(tmp_path)

    expected_seconds = [0, 1, 2, 4, 5, 6, 7, 8, 9]
    assert seconds_by_name(tmp_path) == {f"{index:04}.jpg": second for index, second in enumerate(expected_seconds)}


def test_renumbering_forward_keeps_all_files(tmp_path: Path) -> None:
    make_series(tmp_path, 10)
    (tmp_path / "0003.jpg").unlink()

    run_sequence(tmp_path, start=1)

    expected_seconds = [0, 1, 2, 4, 5, 6, 7, 8, 9]
    expected = {f"{index:04}.jpg": second for index, second in enumerate(expected_seconds, start=1)}
    assert seconds_by_name(tmp_path) == expected


def test_renumbering_without_gap_shifts_forward(tmp_path: Path) -> None:
    make_series(tmp_path, 5)

    run_sequence(tmp_path, start=1)

    assert seconds_by_name(tmp_path) == {f"{index + 1:04}.jpg": index for index in range(5)}


def test_prefix_change_renames_all(tmp_path: Path) -> None:
    make_series(tmp_path, 3)
    run_sequence(tmp_path, prefix="old")

    run_sequence(tmp_path, prefix="new")

    assert seconds_by_name(tmp_path) == {f"new_{index:04}.jpg": index for index in range(3)}


def test_prefix_removal_renames_back(tmp_path: Path) -> None:
    make_series(tmp_path, 3)
    run_sequence(tmp_path, prefix="party")

    run_sequence(tmp_path)

    assert seconds_by_name(tmp_path) == {f"{index:04}.jpg": index for index in range(3)}
