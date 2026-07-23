"""
Unit tests for the pure block/XML operations in timelapse_xml_ops.

These exercise each helper in isolation on hand-written snippets, without going
through the whole generator: the queries on a not-yet-integrated section, the
whole-project edits on a small Xml, and the id-remapping done when cloning.

Per-block operations are not here — they belong to their model class and are
tested in test_timelapse_model.
"""

import re
import uuid

import pytest

from justin.actions.timelapse_xml import Xml
from justin.actions.timelapse_xml_ops import TimelapseXmlOps


# --------------------------------------------------------------------------- #
# header/text queries
# --------------------------------------------------------------------------- #

class TestQueries:
    def test_block_uid_found(self):
        assert TimelapseXmlOps.block_uid('<Foo ObjectUID="abc-123" ClassID="x"/>') == "abc-123"

    def test_block_uid_missing(self):
        assert TimelapseXmlOps.block_uid("<Foo ObjectID=\"5\"/>") is None

    def test_clip_project_item_uid_found(self):
        text = '\t<ClipProjectItem ObjectUID="panel-uid" Version="1">'
        assert TimelapseXmlOps.clip_project_item_uid(text) == "panel-uid"

    def test_clip_project_item_uid_requires_exact_tag(self):
        # A different tag carrying ObjectUID must not match.
        assert TimelapseXmlOps.clip_project_item_uid('<MasterClip ObjectUID="x">') is None

    def test_audio_clip_track_item_id_found(self):
        assert TimelapseXmlOps.audio_clip_track_item_id('<AudioClipTrackItem ObjectID="57">') == "57"

    def test_audio_clip_track_item_id_missing(self):
        assert TimelapseXmlOps.audio_clip_track_item_id('<VideoClipTrackItem ObjectID="57">') is None


def _dump(xml: Xml) -> str:
    return xml.text




class TestClearAudioCachePaths:
    def test_blanks_both_paths(self):
        xml = Xml(
            "<ConformedAudioPath>/Users/x/a.cfa</ConformedAudioPath>"
            "<PeakFilePath>/Users/x/a.pek</PeakFilePath>"
        )
        TimelapseXmlOps.clear_audio_cache_paths(xml)
        assert _dump(xml) == (
            "<ConformedAudioPath></ConformedAudioPath><PeakFilePath></PeakFilePath>"
        )

    def test_blanks_every_occurrence(self):
        xml = Xml(
            "<ConformedAudioPath>/one.cfa</ConformedAudioPath>"
            "<ConformedAudioPath>/two.cfa</ConformedAudioPath>"
        )
        TimelapseXmlOps.clear_audio_cache_paths(xml)
        assert ".cfa" not in _dump(xml)

    def test_already_empty_is_noop(self):
        xml = Xml("<ConformedAudioPath></ConformedAudioPath>")
        TimelapseXmlOps.clear_audio_cache_paths(xml)
        assert _dump(xml) == "<ConformedAudioPath></ConformedAudioPath>"


class TestAppendTrackItemsAfter:
    def test_appends_after_last_continuing_index(self):
        xml = Xml(
            '<TrackItems Version="1">\n'
            '\t\t\t\t\t<TrackItem Index="0" ObjectRef="10"/>\n'
            '\t\t\t\t\t<TrackItem Index="1" ObjectRef="20"/>\n'
            '\t\t\t\t</TrackItems>'
        )
        TimelapseXmlOps.append_track_items_after(xml, anchor_id="10", new_ids=["30", "40"])
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
        TimelapseXmlOps.append_track_items_after(xml, anchor_id="99", new_ids=["50"])
        result = _dump(xml)
        first, second = result.split("</TrackItems>")[:2]
        assert 'ObjectRef="50"' not in first
        assert 'ObjectRef="50"' in second


# --------------------------------------------------------------------------- #
# block-cluster operations
# --------------------------------------------------------------------------- #

class TestRecountIds:
    def test_shifts_numeric_ids(self):
        section = '\t<Media ObjectID="5"><Sub ObjectRef="5"/></Media>\n'
        result = TimelapseXmlOps.recount_ids(section, id_offset=100)
        assert 'ObjectID="105"' in result and 'ObjectRef="105"' in result

    def test_leaves_classid_untouched(self):
        section = (
            '<Media ObjectID="5" ClassID="cccccccc-cccc-cccc-cccc-cccccccccccc">'
            '<Name>x</Name></Media>'
        )
        result = TimelapseXmlOps.recount_ids(section, id_offset=1)
        assert "cccccccc-cccc-cccc-cccc-cccccccccccc" in result

    def test_regenerates_identity_uuids_freshly(self):
        old_uid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        section = (
            f'<Media ObjectID="1" ObjectUID="{old_uid}">'
            f'<Ref ObjectURef="{old_uid}"/><ID>{old_uid}</ID></Media>'
        )
        result = TimelapseXmlOps.recount_ids(section, id_offset=1)
        assert old_uid not in result
        # ObjectUID and ObjectURef pointing at the same old uid remap consistently.
        new_uid = re.search(r'ObjectUID="([^"]+)"', result).group(1)
        assert f'ObjectURef="{new_uid}"' in result
        assert f"<ID>{new_uid}</ID>" in result
        uuid.UUID(new_uid)  # is a valid uuid

    def test_bare_number_in_name_survives(self):
        # A bare "5" in a Name must survive; only ObjectID/ObjectRef="5" shift.
        section = '<Media ObjectID="5"><Name>track5.mp3</Name></Media>'
        result = TimelapseXmlOps.recount_ids(section, id_offset=100)
        assert "<Name>track5.mp3</Name>" in result
        assert 'ObjectID="105"' in result
