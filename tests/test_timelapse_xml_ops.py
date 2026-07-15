"""
Unit tests for the pure block/XML operations in timelapse_xml_ops.

These exercise each helper in isolation on hand-written snippets, without going
through the whole generator: the header queries, the block-text edits, the
whole-project edits on a small Xml, and the block-cluster operations.
"""

import re
import uuid

import pytest

from justin.actions.timelapse_block import Block
from justin.actions.timelapse_xml import Xml
from justin.actions.timelapse_xml_ops import (
    block_uid,
    clip_project_item_uid,
    audio_clip_track_item_id,
    subclip_ref,
    clip_ref,
    block_name,
    set_slot_position,
    set_out_point,
    clear_audio_cache_paths,
    remove_track_item_lines,
    append_track_items_after,
    clone_sound_blocks,
)


# --------------------------------------------------------------------------- #
# header/text queries
# --------------------------------------------------------------------------- #

class TestQueries:
    def test_block_uid_found(self):
        assert block_uid('<Foo ObjectUID="abc-123" ClassID="x"/>') == "abc-123"

    def test_block_uid_missing(self):
        assert block_uid("<Foo ObjectID=\"5\"/>") is None

    def test_clip_project_item_uid_found(self):
        text = '\t<ClipProjectItem ObjectUID="panel-uid" Version="1">'
        assert clip_project_item_uid(text) == "panel-uid"

    def test_clip_project_item_uid_requires_exact_tag(self):
        # A different tag carrying ObjectUID must not match.
        assert clip_project_item_uid('<MasterClip ObjectUID="x">') is None

    def test_audio_clip_track_item_id_found(self):
        assert audio_clip_track_item_id('<AudioClipTrackItem ObjectID="57">') == "57"

    def test_audio_clip_track_item_id_missing(self):
        assert audio_clip_track_item_id('<VideoClipTrackItem ObjectID="57">') is None

    def test_subclip_ref(self):
        assert subclip_ref('<SubClip ObjectRef="42"/>') == "42"
        assert subclip_ref("<Other/>") is None

    def test_clip_ref(self):
        assert clip_ref('<Clip ObjectRef="99"/>') == "99"
        assert clip_ref("<Other/>") is None

    def test_block_name(self):
        assert block_name("<Name>snejnye_volki.mp4</Name>") == "snejnye_volki.mp4"
        assert block_name("<NoName/>") is None

    def test_block_name_first_match_only(self):
        assert block_name("<Name>first</Name><Name>second</Name>") == "first"


# --------------------------------------------------------------------------- #
# block-text edits
# --------------------------------------------------------------------------- #

class TestSetSlotPosition:
    def test_replaces_start_and_end(self):
        slot = "<Start>100</Start>\n\t\t\t\t<End>200</End>"
        result = set_slot_position(slot, start=500, end=900)
        assert "<Start>500</Start>" in result
        assert "<End>900</End>" in result
        assert "100" not in result and "200" not in result

    def test_adds_start_where_first_slot_had_none(self):
        # The first slot (tick 0) has no explicit Start tag.
        slot = "<End>200</End>"
        result = set_slot_position(slot, start=500, end=900)
        assert result == "<Start>500</Start>\n\t\t\t\t<End>900</End>"

    def test_no_start_when_start_is_none(self):
        slot = "<Start>100</Start>\n\t\t\t\t<End>200</End>"
        result = set_slot_position(slot, start=None, end=900)
        assert result == "<End>900</End>"

    def test_only_first_occurrence(self):
        slot = "<End>1</End> ... <End>2</End>"
        result = set_slot_position(slot, start=None, end=9)
        assert result == "<End>9</End> ... <End>2</End>"


class TestSetOutPoint:
    def test_replaces_value(self):
        assert set_out_point("<OutPoint>1</OutPoint>", 42) == "<OutPoint>42</OutPoint>"

    def test_only_first_occurrence(self):
        text = "<OutPoint>1</OutPoint><OutPoint>2</OutPoint>"
        assert set_out_point(text, 9) == "<OutPoint>9</OutPoint><OutPoint>2</OutPoint>"

    def test_no_outpoint_left_untouched(self):
        assert set_out_point("<Nothing/>", 9) == "<Nothing/>"


# --------------------------------------------------------------------------- #
# whole-project edits
# --------------------------------------------------------------------------- #

def _dump(xml: Xml) -> str:
    # Round-trips through toplevel access; Xml has no public getter, so read the field.
    return xml._xml


class TestClearAudioCachePaths:
    def test_blanks_both_paths(self):
        xml = Xml(
            "<ConformedAudioPath>/Users/x/a.cfa</ConformedAudioPath>"
            "<PeakFilePath>/Users/x/a.pek</PeakFilePath>"
        )
        clear_audio_cache_paths(xml)
        assert _dump(xml) == (
            "<ConformedAudioPath></ConformedAudioPath><PeakFilePath></PeakFilePath>"
        )

    def test_blanks_every_occurrence(self):
        xml = Xml(
            "<ConformedAudioPath>/one.cfa</ConformedAudioPath>"
            "<ConformedAudioPath>/two.cfa</ConformedAudioPath>"
        )
        clear_audio_cache_paths(xml)
        assert ".cfa" not in _dump(xml)

    def test_already_empty_is_noop(self):
        xml = Xml("<ConformedAudioPath></ConformedAudioPath>")
        clear_audio_cache_paths(xml)
        assert _dump(xml) == "<ConformedAudioPath></ConformedAudioPath>"


class TestRemoveTrackItemLines:
    def test_removes_named_ids_only(self):
        xml = Xml(
            '\t\t\t\t\t<TrackItem Index="0" ObjectRef="10"/>\n'
            '\t\t\t\t\t<TrackItem Index="1" ObjectRef="20"/>\n'
            '\t\t\t\t\t<TrackItem Index="2" ObjectRef="30"/>\n'
        )
        remove_track_item_lines(xml, ["10", "30"])
        result = _dump(xml)
        assert 'ObjectRef="20"' in result
        assert 'ObjectRef="10"' not in result
        assert 'ObjectRef="30"' not in result
        # No blank line left where a slot was removed.
        assert "\n\n" not in result

    def test_empty_list_is_noop(self):
        original = '\t<TrackItem Index="0" ObjectRef="10"/>\n'
        xml = Xml(original)
        remove_track_item_lines(xml, [])
        assert _dump(xml) == original


class TestAppendTrackItemsAfter:
    def test_appends_after_last_continuing_index(self):
        xml = Xml(
            '<TrackItems Version="1">\n'
            '\t\t\t\t\t<TrackItem Index="0" ObjectRef="10"/>\n'
            '\t\t\t\t\t<TrackItem Index="1" ObjectRef="20"/>\n'
            '\t\t\t\t</TrackItems>'
        )
        append_track_items_after(xml, anchor_id="10", new_ids=["30", "40"])
        result = _dump(xml)
        assert '<TrackItem Index="2" ObjectRef="30"/>' in result
        assert '<TrackItem Index="3" ObjectRef="40"/>' in result

    def test_targets_the_block_containing_anchor(self):
        # Two tracks; only the one holding the anchor slot must grow.
        xml = Xml(
            '<TrackItems Version="1">\n'
            '\t<TrackItem Index="0" ObjectRef="10"/>\n'
            '</TrackItems>'
            '<TrackItems Version="1">\n'
            '\t<TrackItem Index="0" ObjectRef="99"/>\n'
            '</TrackItems>'
        )
        append_track_items_after(xml, anchor_id="99", new_ids=["50"])
        result = _dump(xml)
        first, second = result.split("</TrackItems>")[:2]
        assert 'ObjectRef="50"' not in first
        assert 'ObjectRef="50"' in second


# --------------------------------------------------------------------------- #
# block-cluster operations
# --------------------------------------------------------------------------- #

def _block(idx: int, tag: str, body: str) -> Block:
    return Block(idx, idx, tag, body)


class TestCloneSoundBlocks:
    def test_renames_and_shifts_numeric_ids(self):
        block = _block(
            0, "Media",
            '\t<Media ObjectID="5"><Name>old.mp3</Name><Sub ObjectRef="5"/></Media>\n',
        )
        clone = clone_sound_blocks([block], "old.mp3", "new.mp3", id_offset=100)
        assert "new.mp3" in clone and "old.mp3" not in clone
        assert 'ObjectID="105"' in clone and 'ObjectRef="105"' in clone

    def test_leaves_classid_untouched(self):
        block = _block(
            0, "Media",
            '<Media ObjectID="5" ClassID="cccccccc-cccc-cccc-cccc-cccccccccccc">'
            '<Name>old</Name></Media>',
        )
        clone = clone_sound_blocks([block], "old", "new", id_offset=1)
        assert "cccccccc-cccc-cccc-cccc-cccccccccccc" in clone

    def test_regenerates_identity_uuids_freshly(self):
        old_uid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        block = _block(
            0, "Media",
            f'<Media ObjectID="1" ObjectUID="{old_uid}">'
            f'<Ref ObjectURef="{old_uid}"/><ID>{old_uid}</ID><Name>x</Name></Media>',
        )
        clone = clone_sound_blocks([block], "x", "y", id_offset=1)
        assert old_uid not in clone
        # ObjectUID and ObjectURef pointing at the same old uid remap consistently.
        new_uid = re.search(r'ObjectUID="([^"]+)"', clone).group(1)
        assert f'ObjectURef="{new_uid}"' in clone
        assert f"<ID>{new_uid}</ID>" in clone
        uuid.UUID(new_uid)  # is a valid uuid

    def test_numeric_id_only_remapped_inside_attributes(self):
        # A bare "5" in a Name must survive; only ObjectID/ObjectRef="5" shift.
        block = _block(
            0, "Media",
            '<Media ObjectID="5"><Name>track5.mp3</Name></Media>',
        )
        clone = clone_sound_blocks([block], "track5.mp3", "track5.mp3", id_offset=100)
        assert "<Name>track5.mp3</Name>" in clone
        assert 'ObjectID="105"' in clone
