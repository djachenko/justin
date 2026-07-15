"""
Unit tests for the Sound hierarchy.

AudioSound.adapt strips the video half that the template's mp4 sound carries,
so a plain audio file (mp3, wav, …) ends up with an audio-only structure. These
tests drive adapt on a small synthetic mp4-shaped project and assert exactly
what survives.
"""

from pathlib import Path

import pytest

from justin.actions.timelapse_sound import Sound, AudioSound, VideoSound
from justin.actions.timelapse_xml import Xml


def _dump(xml: Xml) -> str:
    return xml._xml


# A minimal mp4-shaped project: the Media has both a video and an audio stream,
# the MasterClip lists the VideoClip (slot 0) and AudioClip (slot 1), and both
# clips share one Markers chunk (id 30) that must NOT be removed with the video.
def _mp4_project(name: str) -> Xml:
    return Xml(
        "<Project>\n"
        '\t<Media ObjectID="1">\n'
        f'\t\t<Name>{name}</Name>\n'
        '\t\t<VideoStream ObjectRef="10"/>\n'
        '\t\t<AudioStream ObjectRef="11"/>\n'
        '\t</Media>\n'
        '\t<VideoStream ObjectID="10"/>\n'
        '\t<AudioStream ObjectID="11"/>\n'
        '\t<MasterClip ObjectID="2">\n'
        f'\t\t<Name>{name}</Name>\n'
        '\t\t<Clip Index="0" ObjectRef="20"/>\n'
        '\t\t<Clip Index="1" ObjectRef="21"/>\n'
        '\t</MasterClip>\n'
        '\t<VideoClip ObjectID="20">\n'
        '\t\t<Markers ObjectRef="30"/>\n'
        '\t</VideoClip>\n'
        '\t<AudioClip ObjectID="21">\n'
        '\t\t<Markers ObjectRef="30"/>\n'
        '\t</AudioClip>\n'
        '\t<Markers ObjectID="30"/>\n'
        "</Project>\n"
    )


# --------------------------------------------------------------------------- #
# from_path dispatch
# --------------------------------------------------------------------------- #

class TestFromPath:
    def test_audio_extension_gives_audiosound(self):
        assert isinstance(Sound.from_path(Path("x.mp3")), AudioSound)

    def test_video_extension_gives_videosound(self):
        assert isinstance(Sound.from_path(Path("x.mp4")), VideoSound)

    def test_extension_is_case_insensitive(self):
        assert isinstance(Sound.from_path(Path("x.WAV")), AudioSound)

    def test_unsupported_extension_raises(self):
        with pytest.raises(ValueError):
            Sound.from_path(Path("x.txt"))


# --------------------------------------------------------------------------- #
# AudioSound.adapt — the video-stripping logic
# --------------------------------------------------------------------------- #

class TestAudioSoundAdapt:
    def test_strips_video_side_keeps_audio_and_shared(self):
        xml = _mp4_project("song.mp3")
        AudioSound(Path("song.mp3")).adapt(xml)
        result = _dump(xml)

        # Video-only chunks gone: the VideoStream block and the VideoClip block.
        assert '<VideoStream ObjectID="10"/>' not in result
        assert 'ObjectID="20"' not in result  # VideoClip
        # The Media no longer points at the video stream.
        assert '<VideoStream ObjectRef="10"/>' not in result

        # Audio side survives untouched.
        assert '<AudioStream ObjectID="11"/>' in result
        assert 'ObjectID="21"' in result  # AudioClip
        # Shared Markers (referenced by the surviving AudioClip) is kept.
        assert '<Markers ObjectID="30"/>' in result

    def test_masterclip_promotes_audio_to_slot_zero(self):
        xml = _mp4_project("song.mp3")
        AudioSound(Path("song.mp3")).adapt(xml)
        result = _dump(xml)

        # The VideoClip entry is gone and the AudioClip moves from slot 1 to slot 0.
        assert '<Clip Index="0" ObjectRef="20"/>' not in result
        assert '<Clip Index="1" ObjectRef="21"/>' not in result
        assert '<Clip Index="0" ObjectRef="21"/>' in result

    def test_noop_when_media_absent(self):
        xml = _mp4_project("song.mp3")
        before = _dump(xml)
        # A sound whose name isn't in the project — nothing matches, nothing changes.
        AudioSound(Path("other.mp3")).adapt(xml)
        assert _dump(xml) == before

    def test_noop_when_already_audio_only(self):
        # A Media with no VideoStream pointer: adapt must return early.
        xml = Xml(
            "<Project>\n"
            '\t<Media ObjectID="1">\n'
            '\t\t<Name>song.mp3</Name>\n'
            '\t\t<AudioStream ObjectRef="11"/>\n'
            '\t</Media>\n'
            "</Project>\n"
        )
        before = _dump(xml)
        AudioSound(Path("song.mp3")).adapt(xml)
        assert _dump(xml) == before


# --------------------------------------------------------------------------- #
# VideoSound.adapt — no structural change for native mp4
# --------------------------------------------------------------------------- #

def test_videosound_adapt_is_noop():
    xml = _mp4_project("clip.mp4")
    before = _dump(xml)
    VideoSound(Path("clip.mp4")).adapt(xml)
    assert _dump(xml) == before
