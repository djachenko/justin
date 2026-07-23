"""
Unit tests for the typed overlay in timelapse_model.

Two things matter here and are easy to get wrong, so they are tested directly:
dispatch keys on ``ClassID`` (not on the tag, which is not unique per class), and
a numeric reference is only resolvable together with its class (the same number
names different objects of different classes).

The last test checks the hardcoded ``ClassID`` constants against the real
template, so a wrong or stale uuid cannot pass silently.
"""

import pytest

from justin.actions import timelapse_model as model
from justin.actions.timelapse_model import (
    AmbiguousReference,
    AudioClip,
    AudioClipTrackItem,
    AudioStream,
    Clip,
    ClipProjectItem,
    Document,
    MasterClip,
    Media,
    NumericObject,
    OpaqueObject,
    PremiereObject,
    SubClip,
    parse,
    UuidObject,
    VideoClip,
    VideoStream,
)
from justin.actions.timelapse_prproj import _TEMPLATE_DATA
from justin.actions.timelapse_xml import Xml


def build(*blocks: str) -> Document:
    """A minimal document out of hand-written top-level blocks."""
    return Document(Xml("".join(blocks)).toplevel_blocks())


def block(tag: str, class_uuid: str, ident: str, body: str = "") -> str:
    if ident.isdigit():
        identity = f'ObjectID="{ident}"'
    else:
        identity = f'ObjectUID="{ident}"'

    return f'\t<{tag} {identity} ClassID="{class_uuid}" Version="1">\n\t\t{body}\n\t</{tag}>\n'


AUDIO_CLIP = AudioClip.CLASS.uuid
VIDEO_CLIP = VideoClip.CLASS.uuid
MASTER_CLIP = MasterClip.CLASS.uuid


class TestDispatch:
    def test_known_class_id_gives_its_model_class(self):
        doc = build(block("AudioClip", AUDIO_CLIP, "5"))

        assert isinstance(list(doc)[0], AudioClip)

    def test_dispatch_is_by_class_id_not_by_tag(self):
        # Tag says VideoClip, ClassID says AudioClip. ClassID wins: tag → ClassID
        # is one-to-many, so the tag alone cannot identify the type.
        doc = build(block("VideoClip", AUDIO_CLIP, "5"))

        assert isinstance(list(doc)[0], AudioClip)

    def test_unknown_class_id_is_opaque(self):
        doc = build(block("AudioComponentParam", "32657501-3aa4-445f-a49b-d09ecb9fa1ae", "9"))

        assert type(list(doc)[0]) is OpaqueObject

    def test_element_without_class_id_is_opaque(self):
        # The bare forward reference at the top of every project.
        doc = build('\t<Project ObjectRef="1"/>\n')

        assert type(list(doc)[0]) is OpaqueObject

    def test_opaque_still_reads_tag_and_identity(self):
        doc = build(block("AudioComponentParam", "32657501-3aa4-445f-a49b-d09ecb9fa1ae", "9"))
        obj = list(doc)[0]

        assert obj.tag == "AudioComponentParam"
        assert obj.identity == "9"


class TestIdentitySchemes:
    def test_numeric_identity_comes_from_object_id(self):
        doc = build(block("AudioClip", AUDIO_CLIP, "42"))
        obj = list(doc)[0]

        assert isinstance(obj, NumericObject)
        assert obj.identity == "42"

    def test_uuid_identity_comes_from_object_uid(self):
        uid = "cb4e0ed7-aca1-4171-8525-e3658dec06dd"
        doc = build(block("ClipProjectItem", ClipProjectItem.CLASS.uuid, uid))
        obj = list(doc)[0]

        assert isinstance(obj, UuidObject)
        assert obj.identity == uid

    def test_uuid_classes_carry_no_object_id(self):
        # The schemes are mutually exclusive: a UuidObject has no number at all.
        doc = build(block("MasterClip", MASTER_CLIP, "fb11c33a-b0a9-4465-aa94-b6d5db2628cf"))

        assert list(doc)[0].block.id is None


class TestAccessors:
    def test_name_is_none_when_absent(self):
        doc = build(block("AudioClip", AUDIO_CLIP, "5"))

        assert list(doc)[0].name is None

    def test_class_uuid_is_none_on_a_non_object(self):
        doc = build('\t<Project ObjectRef="1"/>\n')

        assert list(doc)[0].class_uuid is None

    def test_refs_and_urefs_do_not_bleed_into_each_other(self):
        # "ObjectRef=" is a near-substring of "ObjectURef=", so a pattern widened
        # on either side starts collecting the other kind of pointer. Checked
        # against exactly that: widening OBJECT_REF to any quoted value, making its
        # "U" optional, or loosening OBJECT_UREF all fail this assertion.
        uid = "12345678-1742-46ec-8663-cda9858b0596"
        doc = build(block(
            "MasterClip", MASTER_CLIP, "fb11c33a-b0a9-4465-aa94-b6d5db2628cf",
            f'<Clip ObjectRef="56"/><Media ObjectURef="{uid}"/>',
        ))
        obj = list(doc)[0]

        assert obj.refs == {"56"}
        assert obj.urefs == {uid}

    def test_refs_collects_every_pointer_once(self):
        doc = build(block(
            "AudioClip", AUDIO_CLIP, "5",
            '<Source ObjectRef="7"/><Content ObjectRef="9"/><Markers ObjectRef="7"/>',
        ))

        assert list(doc)[0].refs == {"7", "9"}

    def test_no_pointers_gives_empty_sets(self):
        doc = build(block("AudioClip", AUDIO_CLIP, "5"))
        obj = list(doc)[0]

        assert obj.refs == set()
        assert obj.urefs == set()

    def test_parse_dispatches_a_lone_block(self):
        # Document goes through parse, but the entry point is public on its own.
        raw = block("AudioClip", AUDIO_CLIP, "5")
        parsed = parse(Xml(raw).toplevel_blocks()[0])

        assert isinstance(parsed, AudioClip)
        assert parsed.identity == "5"


class TestLookup:
    def test_by_ref_needs_the_class_to_disambiguate(self):
        # Same number 7, two different classes — exactly the collision the format
        # allows. Resolving by number alone would be ambiguous.
        doc = build(
            block("AudioClip", AUDIO_CLIP, "7", "<Name>audio</Name>"),
            block("VideoClip", VIDEO_CLIP, "7", "<Name>video</Name>"),
        )

        assert doc.by_ref(AudioClip, "7").name == "audio"
        assert doc.by_ref(VideoClip, "7").name == "video"

    def test_by_ref_missing_returns_none(self):
        doc = build(block("AudioClip", AUDIO_CLIP, "7"))

        assert doc.by_ref(AudioClip, "999") is None
        assert doc.by_ref(AudioClip, None) is None

    def test_by_uref_needs_no_class(self):
        uid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        doc = build(block("MasterClip", MASTER_CLIP, uid, "<Name>master</Name>"))

        assert doc.by_uref(uid).name == "master"
        assert doc.by_uref("no-such-uid") is None

    def test_of_type_filters(self):
        doc = build(
            block("AudioClip", AUDIO_CLIP, "1"),
            block("AudioClip", AUDIO_CLIP, "2"),
            block("VideoClip", VIDEO_CLIP, "3"),
        )

        assert len(doc.of_type(AudioClip)) == 2
        assert len(doc.of_type(VideoClip)) == 1


class TestEdges:
    def test_numeric_edge_resolves(self):
        doc = build(
            block("AudioClipTrackItem", AudioClipTrackItem.CLASS.uuid, "88", '<SubClip ObjectRef="104"/>'),
            block("SubClip", SubClip.CLASS.uuid, "104", "<Name>x.mp3</Name>"),
        )

        assert doc.of_type(AudioClipTrackItem)[0].subclip.identity == "104"

    def test_media_streams_split(self):
        uid = "cccccccc-dddd-eeee-ffff-000000000000"
        doc = build(
            block("Media", Media.CLASS.uuid, uid, '<VideoStream ObjectRef="73"/><AudioStream ObjectRef="80"/>'),
            block("VideoStream", VideoStream.CLASS.uuid, "73"),
            block("AudioStream", AudioStream.CLASS.uuid, "80"),
        )
        media = doc.of_type(Media)[0]

        assert media.video_stream.identity == "73"
        assert media.audio_stream.identity == "80"

    def test_edge_is_none_when_pointer_absent(self):
        # A media with no video stream (audio-only) — the edge simply finds nothing.
        uid = "cccccccc-dddd-eeee-ffff-000000000000"
        doc = build(block("Media", Media.CLASS.uuid, uid, '<AudioStream ObjectRef="80"/>'))

        assert doc.of_type(Media)[0].video_stream is None

    def test_edge_is_none_without_a_document(self):
        # Parsed on its own, an object has no document to resolve edges against.
        raw = block("AudioClipTrackItem", AudioClipTrackItem.CLASS.uuid, "88", '<SubClip ObjectRef="104"/>')
        lone = parse(Xml(raw).toplevel_blocks()[0])

        assert lone.subclip is None

    def test_edge_return_type_is_honest(self):
        doc = build(
            block("AudioClipTrackItem", AudioClipTrackItem.CLASS.uuid, "88", '<SubClip ObjectRef="104"/>'),
            block("SubClip", SubClip.CLASS.uuid, "104"),
        )

        assert isinstance(doc.of_type(AudioClipTrackItem)[0].subclip, SubClip)


class TestPolymorphicClipEdges:
    def test_clip_edge_resolves_to_whichever_half(self):
        # Same `.clip` edge, different concrete type per instance: <Clip> is a role,
        # and the target's ClassID (not the ref tag) decides audio vs video.
        doc = build(
            block("SubClip", SubClip.CLASS.uuid, "97", '<Clip ObjectRef="113"/>'),
            block("SubClip", SubClip.CLASS.uuid, "104", '<Clip ObjectRef="117"/>'),
            block("VideoClip", VIDEO_CLIP, "113"),
            block("AudioClip", AUDIO_CLIP, "117"),
        )
        subs = {sub.identity: sub for sub in doc.of_type(SubClip)}

        assert isinstance(subs["97"].clip, VideoClip)
        assert isinstance(subs["104"].clip, AudioClip)

    def test_master_clip_lists_its_halves_in_slot_order(self):
        uid = "dddddddd-eeee-ffff-0000-111111111111"
        doc = build(
            block("MasterClip", MASTER_CLIP, uid,
                  '<Clip Index="0" ObjectRef="55"/><Clip Index="1" ObjectRef="56"/>'),
            block("VideoClip", VIDEO_CLIP, "55"),
            block("AudioClip", AUDIO_CLIP, "56"),
        )
        clips = doc.of_type(MasterClip)[0].clips

        assert [type(clip) for clip in clips] == [VideoClip, AudioClip]

    def test_base_class_lookup_fails_loud_on_collision(self):
        # Audio and video clip numbered alike — the base-class lookup refuses to
        # guess which the ref means, rather than silently pick one.
        doc = build(
            block("AudioClip", AUDIO_CLIP, "7"),
            block("VideoClip", VIDEO_CLIP, "7"),
        )

        with pytest.raises(AmbiguousReference):
            doc.by_ref(Clip, "7")

    def test_leaf_class_lookup_is_unaffected_by_collision(self):
        # The same "7" resolves fine when a concrete class is named — ObjectID is
        # unique within one ClassID.
        doc = build(
            block("AudioClip", AUDIO_CLIP, "7"),
            block("VideoClip", VIDEO_CLIP, "7"),
        )

        assert doc.by_ref(AudioClip, "7").identity == "7"
        assert isinstance(doc.by_ref(AudioClip, "7"), AudioClip)


class TestAgainstRealTemplate:
    def document(self) -> Document:
        return Document(Xml.from_gzip_bytes(_TEMPLATE_DATA).toplevel_blocks())

    def test_slot_navigates_to_its_subclip(self):
        doc = self.document()
        slot = doc.of_type(AudioClipTrackItem)[0]

        assert isinstance(slot.subclip, SubClip)

    def test_every_subclip_resolves_to_a_clip(self):
        doc = self.document()

        for sub in doc.of_type(SubClip):
            assert isinstance(sub.clip, Clip)

    def test_sound_master_lists_both_halves(self):
        # The sound is an mp4, so its MasterClip has a video and an audio half.
        doc = self.document()
        sound_master = next(
            mc for mc in doc.of_type(MasterClip)
            if any(isinstance(clip, AudioClip) for clip in mc.clips)
        )
        types = {type(clip) for clip in sound_master.clips}

        assert types == {VideoClip, AudioClip}

    def test_sound_media_carries_both_streams(self):
        doc = self.document()
        sound_media = next(md for md in doc.of_type(Media) if "TMPL_SOUND" in md.block.text)

        assert isinstance(sound_media.video_stream, VideoStream)
        assert isinstance(sound_media.audio_stream, AudioStream)

    def test_frames_media_has_no_audio(self):
        # An image sequence has a picture stream but no sound.
        doc = self.document()
        frames_media = next(md for md in doc.of_type(Media) if "TMPL_SOUND" not in md.block.text)

        assert frames_media.audio_stream is None

    def test_every_block_parses(self):
        doc = self.document()

        assert len(doc) > 0
        assert all(isinstance(o, PremiereObject) for o in doc)

    def test_hardcoded_class_ids_match_the_template(self):
        # Guards against a mistyped or stale ClassID constant: for every modelled
        # object found in the real file, the tag and uuid must be what we declared.
        for obj in self.document():
            if type(obj) is OpaqueObject:
                continue

            assert obj.class_uuid == type(obj).CLASS.uuid
            assert obj.tag == type(obj).CLASS.tag

    def test_identity_scheme_holds_in_the_template(self):
        for obj in self.document():
            if isinstance(obj, UuidObject):
                assert obj.block.id is None
            elif isinstance(obj, NumericObject):
                assert obj.identity is not None and obj.identity.isdigit()

    def test_navigates_slot_to_its_audio_clip(self):
        from justin.actions.timelapse_xml_ops import TimelapseXmlOps as ops

        doc = self.document()
        slot = doc.of_type(AudioClipTrackItem)[0]
        subclip = doc.by_ref(SubClip, ops.subclip_ref(slot.block.text))
        audio_clip = doc.by_ref(AudioClip, ops.clip_ref(subclip.block.text))

        assert subclip is not None
        assert audio_clip is not None
        assert subclip.name is not None

    def test_registry_covers_every_modelled_class_once(self):
        registry = PremiereObject._BY_CLASS_UUID
        modelled = [
            value for value in vars(model).values()
            if isinstance(value, type)
            and issubclass(value, PremiereObject)
            and value.CLASS is not None
        ]

        assert len(registry) == len(modelled)
        assert {c.CLASS.uuid for c in modelled} == set(registry)
