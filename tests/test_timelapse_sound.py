"""
Unit tests for the Sound hierarchy.

``adapt`` realizes a template section as this sound's own: it renames the
template's placeholder to the sound's filename, and — for audio-only sounds —
strips the video half the mp4 template carries. These tests drive adapt on a
small synthetic mp4-shaped section (still named with the placeholder) and assert
what the realized section looks like.
"""

from pathlib import Path

import pytest

from justin.actions.timelapse_sound import Sound, AudioSound, VideoSound
from justin.actions.timelapse_template import TimelapseTemplate

MARKER = TimelapseTemplate.SOUND_NAME  # the placeholder adapt renames away


# A minimal mp4-shaped section, still named with the template placeholder: the
# Media has both a video and an audio stream, the MasterClip lists the VideoClip
# (slot 0) and AudioClip (slot 1), and both clips share one Markers chunk (id 30)
# that must NOT be removed with the video.
def _mp4_section() -> str:
    return (
        "<Project>\n"
        '\t<Media ObjectID="1">\n'
        f'\t\t<Name>{MARKER}</Name>\n'
        '\t\t<VideoStream ObjectRef="10"/>\n'
        '\t\t<AudioStream ObjectRef="11"/>\n'
        '\t</Media>\n'
        '\t<VideoStream ObjectID="10"/>\n'
        '\t<AudioStream ObjectID="11"/>\n'
        '\t<MasterClip ObjectID="2">\n'
        f'\t\t<Name>{MARKER}</Name>\n'
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
# Sound.rename — the shared base step both subclasses build adapt from
# --------------------------------------------------------------------------- #

class TestRename:
    def test_swaps_placeholder_for_filename_everywhere(self):
        section = f"<Name>{MARKER}</Name> media ./sound/{MARKER}"
        assert AudioSound(Path("song.mp3")).rename(section) == "<Name>song.mp3</Name> media ./sound/song.mp3"

    def test_same_rename_for_video_and_audio(self):
        section = f"<Name>{MARKER}</Name>"
        assert VideoSound(Path("clip.mp4")).rename(section) == "<Name>clip.mp4</Name>"


# --------------------------------------------------------------------------- #
# AudioSound.adapt — rename + video-strip
# --------------------------------------------------------------------------- #

class TestAudioSoundAdapt:
    def test_renames_placeholder_to_the_sound_file(self):
        result = AudioSound(Path("song.mp3")).adapt(_mp4_section())
        assert MARKER not in result
        assert "<Name>song.mp3</Name>" in result

    def test_strips_video_side_keeps_audio_and_shared(self):
        result = AudioSound(Path("song.mp3")).adapt(_mp4_section())

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
        result = AudioSound(Path("song.mp3")).adapt(_mp4_section())

        assert '<Clip Index="0" ObjectRef="20"/>' not in result
        assert '<Clip Index="1" ObjectRef="21"/>' not in result
        assert '<Clip Index="0" ObjectRef="21"/>' in result

    def test_already_audio_only_is_renamed_but_not_stripped(self):
        # A Media with no VideoStream pointer: renamed, structure otherwise intact.
        section = (
            "<Project>\n"
            '\t<Media ObjectID="1">\n'
            f'\t\t<Name>{MARKER}</Name>\n'
            '\t\t<AudioStream ObjectRef="11"/>\n'
            '\t</Media>\n'
            "</Project>\n"
        )
        result = AudioSound(Path("song.mp3")).adapt(section)
        assert "<Name>song.mp3</Name>" in result
        assert '<AudioStream ObjectRef="11"/>' in result


# --------------------------------------------------------------------------- #
# VideoSound.adapt — rename only, video kept (native mp4)
# --------------------------------------------------------------------------- #

def test_videosound_adapt_renames_only():
    result = VideoSound(Path("clip.mp4")).adapt(_mp4_section())
    assert "<Name>clip.mp4</Name>" in result        # renamed
    assert '<VideoStream ObjectID="10"/>' in result  # video kept
    assert '<Clip Index="0" ObjectRef="20"/>' in result
