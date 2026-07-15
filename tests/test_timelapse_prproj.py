"""
Structural tests for the timelapse .prproj generator.

These build real projects from the shipped template + synthetic input dirs and
assert the invariants that make Premiere accept the file, without opening
Premiere: well-formed XML, no dangling references, no duplicate object uuids,
consistent per-type ClassIDs on clones, and the expected timeline layout.

``_probe_duration_ticks`` (ffprobe) is monkeypatched so the synthetic sound
files can be empty and tests stay hermetic.
"""

import gzip
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest

from justin.actions import timelapse_prproj as tlp
from justin.actions.timelapse_prproj import (
    PREMIERE_TIMEBASE,
    TimelapseSchema,
    _resolve_timeline_sounds,
    generate_prproj,
    _TEMPLATE_DATA,
)
from justin.actions.timelapse_settings import TimelapseSettings
from justin.actions.timelapse_sources import TimelapseSources
from justin.actions.timelapse_xml import Block, Xml, clone_sound_blocks as _clone_sound_blocks


# --------------------------------------------------------------------------- #
# fixtures / helpers
# --------------------------------------------------------------------------- #

def make_timelapse(
    root: Path,
    photoset: str = "26.05.31.testset",
    n_frames: int = 3,
    cover: bool = True,
    sounds: tuple[str, ...] = ("alpha.mp3", "beta.mp3"),
) -> Path:
    """Create a synthetic <photoset>/timelapse/ tree and return the timelapse dir."""
    timelapse_dir = root / photoset / "timelapse"
    frames_dir = timelapse_dir / "frames"
    frames_dir.mkdir(parents=True)

    for i in range(1, n_frames + 1):
        (frames_dir / f"shot_{i:04}.jpg").write_bytes(b"")

    if cover:
        (timelapse_dir / "cover.jpg").write_bytes(b"")

    if sounds:
        sound_dir = timelapse_dir / "sound"
        sound_dir.mkdir()

        for name in sounds:
            (sound_dir / name).write_bytes(b"")

    return timelapse_dir


@pytest.fixture(autouse=True)
def stub_ffprobe(monkeypatch):
    """Deterministic durations keyed by filename, no ffprobe needed."""
    def fake_duration(path: Path) -> int:
        # Distinct per name so sequential layout is observable.
        return (len(path.name) + 1) * PREMIERE_TIMEBASE
    monkeypatch.setattr(tlp, "_probe_duration_ticks", fake_duration)


def read_project(path: Path) -> str:
    with gzip.open(path, "rb") as f:
        return f.read().decode("utf-8")


def dangling_numeric_refs(xml: str) -> set[str]:
    ids = set(re.findall(r'ObjectID="(\d+)"', xml))
    refs = set(re.findall(r'ObjectRef="(\d+)"', xml))
    return refs - ids


def dangling_uuid_refs(xml: str) -> set[str]:
    uids = set(re.findall(r'ObjectUID="([^"]+)"', xml))
    urefs = set(re.findall(r'ObjectURef="([^"]+)"', xml))
    return urefs - uids


def duplicate_uuids(xml: str) -> list[str]:
    counts = Counter(re.findall(r'ObjectUID="([^"]+)"', xml))
    return [uid for uid, n in counts.items() if n > 1]


def track_item_count(xml: str) -> int:
    return xml.count("<AudioClipTrackItem ")


def panel_item_names(xml: str) -> set[str]:
    return set(re.findall(r"<ClipProjectItem[^>]*>.*?<Name>([^<]+)</Name>", xml, re.DOTALL))


def assert_structurally_sound(xml: str) -> None:
    ET.fromstring(xml)  # raises on malformed XML
    assert not dangling_numeric_refs(xml)
    assert not dangling_uuid_refs(xml)
    assert not duplicate_uuids(xml)


def generate(timelapse_dir: Path, fps: float = 10.0, timeline_sounds: list[str] | None = None) -> str:
    sources = TimelapseSources.from_folder(timelapse_dir.parent.name, timelapse_dir)
    settings = TimelapseSettings(fps=fps, timeline_sounds=timeline_sounds or [])
    out = timelapse_dir / "out.prproj"
    TimelapseSchema()(out, sources, settings)
    return read_project(out)


# --------------------------------------------------------------------------- #
# scenario matrix — every combination must produce an openable project
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("n_sounds", [0, 1, 2])
@pytest.mark.parametrize("cover", [True, False])
@pytest.mark.parametrize("on_timeline", ["none", "all"])
def test_scenario_matrix_is_structurally_sound(tmp_path, n_sounds, cover, on_timeline):
    names = ("alpha.mp3", "beta.mp3")[:n_sounds]
    timelapse_dir = make_timelapse(tmp_path, cover=cover, sounds=names)
    timeline_sounds = list(names) if on_timeline == "all" else []

    xml = generate(timelapse_dir, timeline_sounds=timeline_sounds)

    assert_structurally_sound(xml)
    expected_actis = len(names) if on_timeline == "all" else 0
    assert track_item_count(xml) == expected_actis


# --------------------------------------------------------------------------- #
# panel vs timeline placement
# --------------------------------------------------------------------------- #

def test_all_sounds_land_in_panel_regardless_of_timeline(tmp_path):
    timelapse_dir = make_timelapse(tmp_path, sounds=("alpha.mp3", "beta.mp3"))
    xml = generate(timelapse_dir, timeline_sounds=[])
    assert {"alpha.mp3", "beta.mp3"} <= panel_item_names(xml)


def test_partial_timeline_selection_keeps_only_chosen_sound(tmp_path):
    timelapse_dir = make_timelapse(tmp_path, sounds=("alpha.mp3", "beta.mp3"))
    xml = generate(timelapse_dir, timeline_sounds=["beta"])

    assert track_item_count(xml) == 1
    assert {"alpha.mp3", "beta.mp3"} <= panel_item_names(xml)
    # The single track item must be beta, not alpha.
    blocks = Xml(xml).toplevel_blocks()
    text_by_id = {
        (b.tag, re.search(r'ObjectID="(\d+)"', b.text[:120]).group(1)): b.text
        for b in blocks if re.search(r'ObjectID="(\d+)"', b.text[:120])
    }
    names = [
        TimelapseSchema._track_item_sound_name(b.text, text_by_id)
        for b in blocks if b.tag == "AudioClipTrackItem"
    ]
    assert names == ["beta.mp3"]


def test_timeline_sounds_are_laid_out_sequentially(tmp_path):
    timelapse_dir = make_timelapse(tmp_path, sounds=("alpha.mp3", "beta.mp3"))
    xml = generate(timelapse_dir, timeline_sounds=["alpha", "beta"])

    alpha_dur = (len("alpha.mp3") + 1) * PREMIERE_TIMEBASE
    beta_dur = (len("beta.mp3") + 1) * PREMIERE_TIMEBASE

    ends = [int(e) for e in re.findall(r"<End>(\d+)</End>", _audio_track_items_region(xml))]
    starts = [int(s) for s in re.findall(r"<Start>(\d+)</Start>", _audio_track_items_region(xml))]
    # First clip ends at its own duration; second starts there and ends after both.
    assert alpha_dur in ends
    assert alpha_dur in starts  # second clip starts where the first ended
    assert alpha_dur + beta_dur in ends


def _audio_track_items_region(xml: str) -> str:
    """Concatenated AudioClipTrackItem blocks (where timeline Start/End live)."""
    return "".join(
        b.text for b in Xml(xml).toplevel_blocks() if b.tag == "AudioClipTrackItem"
    )


# --------------------------------------------------------------------------- #
# golden: reproduce the real wolfday template structure
# --------------------------------------------------------------------------- #

def test_reproduces_wolfday_template_structure(tmp_path):
    # The vendored template IS the real wolfday project file (step_12). The
    # generator must reproduce its block structure from equivalent inputs — this
    # keeps us honest even though wolfday's live sources aren't in the repo.
    timelapse_dir = make_timelapse(
        tmp_path, photoset="26.04.17.wolfday",
        n_frames=106, cover=True, sounds=("snejnye_volki.mp4",),
    )
    xml = generate(timelapse_dir, timeline_sounds=["snejnye_volki"])

    template = gzip.decompress(_TEMPLATE_DATA).decode("utf-8")

    def tag_counts(project: str) -> Counter:
        return Counter(b.tag for b in Xml(project).toplevel_blocks())

    assert tag_counts(xml) == tag_counts(template)
    assert_structurally_sound(xml)


# --------------------------------------------------------------------------- #
# clone correctness — the bug that made multi-sound projects fail to open
# --------------------------------------------------------------------------- #

def test_clone_introduces_no_new_classids(tmp_path):
    # The clone bug regenerated ClassIDs (they are uuids), so a clone's blocks
    # carried ClassIDs found nowhere else and Premiere refused to open the file.
    # Guard: every ClassID in the output already exists in the template.
    timelapse_dir = make_timelapse(tmp_path, sounds=("alpha.mp3", "beta.mp3"))
    xml = generate(timelapse_dir, timeline_sounds=["alpha", "beta"])

    template = gzip.decompress(_TEMPLATE_DATA).decode("utf-8")
    template_classids = set(re.findall(r'ClassID="([^"]+)"', template))
    output_classids = set(re.findall(r'ClassID="([^"]+)"', xml))

    assert output_classids <= template_classids
    # ...while object identities are fresh (no duplicate uuids).
    assert not duplicate_uuids(xml)


# --------------------------------------------------------------------------- #
# removal paths — regressions for remove_dangling_refs corruption
# --------------------------------------------------------------------------- #

def test_no_cover_project_is_valid(tmp_path):
    timelapse_dir = make_timelapse(tmp_path, cover=False, sounds=("alpha.mp3",))
    assert_structurally_sound(generate(timelapse_dir, timeline_sounds=[]))


def test_no_sound_project_is_valid(tmp_path):
    timelapse_dir = make_timelapse(tmp_path, sounds=())
    xml = generate(timelapse_dir)
    assert_structurally_sound(xml)
    assert track_item_count(xml) == 0


# --------------------------------------------------------------------------- #
# generate_prproj wrapper
# --------------------------------------------------------------------------- #

def test_generate_numbers_output_instead_of_overwriting(tmp_path):
    timelapse_dir = make_timelapse(tmp_path, photoset="26.05.31.numbered", sounds=("alpha.mp3",))
    sources = TimelapseSources.from_folder(timelapse_dir.parent.name, timelapse_dir)
    first = generate_prproj(sources)
    second = generate_prproj(sources)

    assert first.name == "26.05.31.numbered.prproj"
    assert second.name == "26.05.31.numbered_1.prproj"
    assert first.exists() and second.exists()


def test_selector_matches_by_name_or_stem(tmp_path):
    timelapse_dir = make_timelapse(tmp_path, sounds=("alpha.mp3", "beta.mp3"))
    sources = TimelapseSources.from_folder(timelapse_dir.parent.name, timelapse_dir)
    by_stem = _resolve_timeline_sounds(sources.sounds, ["alpha"])
    by_name = _resolve_timeline_sounds(sources.sounds, ["alpha.mp3"])
    assert [p.name for p in by_stem] == ["alpha.mp3"]
    assert [p.name for p in by_name] == ["alpha.mp3"]


# --------------------------------------------------------------------------- #
# low-level helpers
# --------------------------------------------------------------------------- #

def test_parse_toplevel_blocks_roundtrip():
    xml = "<Project>\n\t<Foo ObjectID=\"1\">\n\t\t<Bar/>\n\t</Foo>\n\t<Baz ObjectID=\"2\"/>\n</Project>\n"
    blocks = Xml(xml).toplevel_blocks()
    assert [b.tag for b in blocks] == ["Foo", "Baz"]
    # Offsets slice the exact block text back out.
    for b in blocks:
        assert xml[b.start:b.end] == b.text


def test_clone_shifts_ids_and_renames():
    block = Block(
        0, 0, "Media",
        '\t<Media ObjectID="5" ClassID="cccccccc-cccc-cccc-cccc-cccccccccccc">'
        '<Name>old.mp3</Name><Sub ObjectRef="5"/></Media>\n',
    )
    clone = _clone_sound_blocks([block], "old.mp3", "new.mp3", id_offset=100)
    assert "new.mp3" in clone and "old.mp3" not in clone
    assert 'ObjectID="105"' in clone and 'ObjectRef="105"' in clone
    # ClassID untouched.
    assert "cccccccc-cccc-cccc-cccc-cccccccccccc" in clone
