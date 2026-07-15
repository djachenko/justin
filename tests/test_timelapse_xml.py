"""
Unit tests for the Xml wrapper and the Block value type.

Xml is the string-manipulation layer under the generator: block parsing, id
queries, in-place edits and the dangling-reference cleanup. These tests drive
each method on small hand-written snippets.
"""

import gzip

from justin.actions.timelapse_block import Block, Blocks
from justin.actions.timelapse_xml import Xml, _CLIP_MEDIA_TYPES


def _dump(xml: Xml) -> str:
    return xml._xml


# --------------------------------------------------------------------------- #
# construction / io round-trip
# --------------------------------------------------------------------------- #

def test_from_and_to_prproj_roundtrip(tmp_path):
    original = "<Project>\n\t<Foo/>\n</Project>\n"
    path = tmp_path / "p.prproj"
    Xml(original).to_prproj(path)
    # File is real gzip.
    assert gzip.decompress(path.read_bytes()).decode("utf-8") == original
    assert _dump(Xml.from_prproj(path)) == original


def test_from_gzip_bytes():
    original = "<Project/>"
    data = gzip.compress(original.encode("utf-8"))
    assert _dump(Xml.from_gzip_bytes(data)) == original


# --------------------------------------------------------------------------- #
# queries
# --------------------------------------------------------------------------- #

def test_max_object_id():
    xml = Xml('<A ObjectID="3"/><B ObjectID="41"/><C ObjectID="7"/>')
    assert xml.max_object_id() == 41


def test_find_panel_item_index_found():
    xml = Xml('<Item Index="0" ObjectURef="x"/><Item Index="5" ObjectURef="target"/>')
    assert xml.find_panel_item_index("target") == 5


def test_find_panel_item_index_missing():
    xml = Xml('<Item Index="0" ObjectURef="x"/>')
    assert xml.find_panel_item_index("nope") is None


def test_find_panel_item_index_escapes_uid():
    # UUIDs contain hyphens; the builder must escape so they're treated literally.
    xml = Xml('<Item Index="2" ObjectURef="a-b-c"/>')
    assert xml.find_panel_item_index("a-b-c") == 2


# --------------------------------------------------------------------------- #
# primitive edits
# --------------------------------------------------------------------------- #

def test_replace():
    xml = Xml("abcabc")
    xml.replace("a", "X")
    assert _dump(xml) == "XbcXbc"


def test_replace_range():
    xml = Xml("0123456789")
    xml.replace_range(2, 5, "__")
    assert _dump(xml) == "01__56789"


def test_insert():
    xml = Xml("0189")
    xml.insert(2, "____")
    assert _dump(xml) == "01____89"


def test_sub_with_count():
    xml = Xml("aaa")
    xml.sub(r"a", "b", count=2)
    assert _dump(xml) == "bba"


# --------------------------------------------------------------------------- #
# block parsing
# --------------------------------------------------------------------------- #

def test_toplevel_blocks_multiline_and_selfclosing():
    xml = "<Project>\n\t<Foo ObjectID=\"1\">\n\t\t<Bar/>\n\t</Foo>\n\t<Baz ObjectID=\"2\"/>\n</Project>\n"
    blocks = Xml(xml).toplevel_blocks()
    assert [b.tag for b in blocks] == ["Foo", "Baz"]
    for b in blocks:
        assert xml[b.start:b.end] == b.text


def test_toplevel_blocks_ignores_deeper_nesting():
    # A nested <Foo> at two tabs must not be picked up as top-level.
    xml = "<Project>\n\t<Outer>\n\t\t<Foo/>\n\t</Outer>\n</Project>\n"
    blocks = Xml(xml).toplevel_blocks()
    assert [b.tag for b in blocks] == ["Outer"]


def test_toplevel_blocks_skips_unclosed():
    xml = "<Project>\n\t<Foo>\n\t\t<Bar/>\n</Project>\n"
    # <Foo> has no matching "\n\t</Foo>" — skipped silently, no crash.
    assert Xml(xml).toplevel_blocks() == []


# --------------------------------------------------------------------------- #
# structural edits
# --------------------------------------------------------------------------- #

def test_remove_blocks_by_positions_cuts_back_to_front():
    xml = Xml("0123456789")
    xml.remove_blocks_by_positions([(1, 3), (5, 7)])
    # Removing (5,7) then (1,3) — offsets stay valid because we cut from the end.
    assert _dump(xml) == "034789"


def test_remove_dangling_numeric_ref_block():
    # SubClip's Source points at id 99 which doesn't exist → the SubClip is removed.
    xml = Xml(
        "<Project>\n"
        '\t<AudioClip ObjectID="1"/>\n'
        '\t<SubClip ObjectID="2">\n'
        '\t\t<Source ObjectRef="99"/>\n'
        '\t</SubClip>\n'
        "</Project>\n"
    )
    xml.remove_dangling_refs()
    result = _dump(xml)
    assert "SubClip" not in result
    assert 'ObjectID="1"' in result


def test_remove_dangling_prunes_panel_item_and_renumbers_track():
    xml = Xml(
        "<Project>\n"
        '\t<AudioClip ObjectID="10" ObjectUID="live"/>\n'
        '\t<Items Version="1">\n'
        '\t\t<Item Index="0" ObjectURef="live"/>\n'
        '\t\t<Item Index="1" ObjectURef="gone"/>\n'
        '\t</Items>\n'
        '\t<TrackItems Version="1">\n'
        '\t\t<TrackItem Index="0" ObjectRef="404"/>\n'
        '\t\t<TrackItem Index="1" ObjectRef="10"/>\n'
        '\t</TrackItems>\n'
        "</Project>\n"
    )
    xml.remove_dangling_refs()
    result = _dump(xml)
    # Stale panel item dropped, live one kept.
    assert 'ObjectURef="gone"' not in result
    assert 'ObjectURef="live"' in result
    # Dangling track slot dropped and survivor renumbered to Index 0.
    assert 'ObjectRef="404"' not in result
    assert '<TrackItem Index="0" ObjectRef="10"/>' in result


def test_remove_dangling_cascades():
    # A points at B, B points at missing id → removing B also strands A.
    xml = Xml(
        "<Project>\n"
        '\t<SubClip ObjectID="1">\n\t\t<Source ObjectRef="2"/>\n\t</SubClip>\n'
        '\t<SubClip ObjectID="2">\n\t\t<Content ObjectRef="404"/>\n\t</SubClip>\n'
        "</Project>\n"
    )
    xml.remove_dangling_refs()
    result = _dump(xml)
    assert "SubClip" not in result


# --------------------------------------------------------------------------- #
# Block value type
# --------------------------------------------------------------------------- #

def test_block_header_truncates():
    long_text = "<Tag " + "x" * 500 + "/>"
    block = Block(0, len(long_text), "Tag", long_text)
    assert len(block.header) == Block._HEADER_LEN


def test_block_id_reads_from_header():
    block = Block(0, 0, "Tag", '\t<Tag ObjectID="77" ClassID="z">body</Tag>')
    assert block.id == "77"


def test_block_id_none_when_absent():
    block = Block(0, 0, "Tag", "<Tag/>")
    assert block.id is None


def test_block_span():
    block = Block(10, 25, "Tag", "text")
    assert block.span == (10, 25)


# --------------------------------------------------------------------------- #
# Blocks.reachable_cluster — walk the reference graph from seed blocks
# --------------------------------------------------------------------------- #

def _blocks(*rows: tuple[str, str]) -> Blocks:
    # Each row is (tag, body); block.start = position, used as the unique key.
    return Blocks(Block(i, i, tag, body) for i, (tag, body) in enumerate(rows))


def _cluster_starts(blocks: Blocks, *seed_starts: int) -> list[int]:
    seeds = [b for b in blocks if b.start in seed_starts]
    return [b.start for b in blocks.reachable_cluster(seeds, _CLIP_MEDIA_TYPES)]


class TestReachableCluster:
    def test_follows_numeric_ref_to_member_block(self):
        blocks = _blocks(
            ("SubClip", '<SubClip ObjectID="1"><Clip ObjectRef="2"/></SubClip>'),
            ("AudioClip", '<AudioClip ObjectID="2"><Name>a.mp3</Name></AudioClip>'),
            ("AudioClip", '<AudioClip ObjectID="3"><Name>other.mp3</Name></AudioClip>'),
        )
        assert _cluster_starts(blocks, 0) == [0, 1]

    def test_follows_uuid_ref_only_to_member_tags(self):
        blocks = _blocks(
            ("Media", '<Media ObjectUID="uid-a"><X ObjectURef="uid-b"/></Media>'),
            ("AudioClip", '<AudioClip ObjectUID="uid-b"/>'),
        )
        assert _cluster_starts(blocks, 0) == [0, 1]

    def test_uuid_ref_to_nonmember_is_ignored(self):
        blocks = _blocks(
            ("Media", '<Media ObjectUID="uid-a"><X ObjectURef="uid-b"/></Media>'),
            ("Sequence", '<Sequence ObjectUID="uid-b"/>'),
        )
        assert _cluster_starts(blocks, 0) == [0]

    def test_numeric_ref_matches_any_member_kind_with_that_id(self):
        # Ambiguous number pointer: both a Video and Audio clip share id 5.
        blocks = _blocks(
            ("SubClip", '<SubClip ObjectID="1"><Clip ObjectRef="5"/></SubClip>'),
            ("VideoClip", '<VideoClip ObjectID="5"/>'),
            ("AudioClip", '<AudioClip ObjectID="5"/>'),
        )
        assert _cluster_starts(blocks, 0) == [0, 1, 2]

    def test_transitive_closure(self):
        blocks = _blocks(
            ("MasterClip", '<MasterClip ObjectID="1"><Clip ObjectRef="2"/></MasterClip>'),
            ("AudioClip", '<AudioClip ObjectID="2"><Media ObjectRef="3"/></AudioClip>'),
            ("Media", '<Media ObjectID="3"/>'),
            ("AudioClip", '<AudioClip ObjectID="9"/>'),
        )
        assert _cluster_starts(blocks, 0) == [0, 1, 2]
