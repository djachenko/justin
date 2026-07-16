from abc import ABC, abstractmethod
from pathlib import Path

from justin.actions.timelapse_tags import Tag
from justin.actions.timelapse_template import TimelapseTemplate
from justin.actions.timelapse_xml import Xml
from justin.actions.timelapse_xml_ops import TimelapseXmlOps

# Formats that carry audio only — no picture. The template's sound is an mp4
# (which has a video part), so clones of these need that video part stripped.
AUDIO_ONLY_EXTENSIONS = {".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg", ".aiff"}
VIDEO_AS_AUDIO_EXTENSIONS = {".mp4"}

# A MasterClip lists its two halves as <Clip Index="N" ...>: slot 0 is the video
# half, slot 1 the audio half — until the video half is stripped for audio-only.
_VIDEO_SLOT = 0
_AUDIO_SLOT = 1


class Sound(ABC):
    @property
    @abstractmethod
    def path(self) -> Path: ...

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def stem(self) -> str:
        return self.path.stem

    @abstractmethod
    def adapt(self, section: str) -> str:
        """Realize a template section as this sound's own — rename the placeholder to
        this sound's file and adapt structure (video stripped for audio-only) — and
        return it (still on template ids; integration assigns fresh ones later).
        Subclasses build this out of ``rename``."""
        ...

    def rename(self, section: str) -> str:
        """Swap the template's placeholder sound name for this sound's real filename."""
        return section.replace(TimelapseTemplate.SOUND_NAME, self.name)

    @classmethod
    def from_path(cls, path: Path) -> "Sound":
        suffix = path.suffix.lower()
        if suffix in AUDIO_ONLY_EXTENSIONS:
            return AudioSound(path)
        elif suffix in VIDEO_AS_AUDIO_EXTENSIONS:
            return VideoSound(path)
        else:
            raise ValueError(f"Unsupported sound format: {path.suffix}")


class AudioSound(Sound):
    """A sound file that carries audio only (mp3, wav, flac, …).

    The template's sound is an mp4, so every clone starts with a video part
    attached. ``adapt`` strips that video half out and returns an audio-only section.
    """

    def __init__(self, path: Path) -> None:
        self.__path = path

    @property
    def path(self) -> Path:
        return self.__path

    def adapt(self, section: str) -> str:
        """Rename to this sound's file, then strip the video half the mp4 template carries.

        The template's sound is an mp4, so a section has both a video part and an
        audio part. A plain audio file has no video, so after renaming we remove:
          * the video-stream pointer from the Media block and the stream itself;
          * the VideoClip and the blocks hanging off it (its markers, its video
            source) — but only the ones the surviving AudioClip doesn't also use
            (a Markers block can be shared);
          * the VideoClip entry in the MasterClip, promoting the AudioClip to slot 0.

        Works on this sound's own section only (nothing outside its cluster) and
        returns the renamed, audio-only section.
        """
        section = self.rename(section)
        fragment = Xml(section)
        media = fragment.toplevel_blocks().containing(self.name).by_tag(Tag.Media).first()

        if media is None:
            return section

        video_stream_id = TimelapseXmlOps.video_stream_ref(media.text)

        if video_stream_id is None:
            return section  # no video part — already audio-only, nothing to do

        fragment.replace_range(*media.span, TimelapseXmlOps.drop_video_stream(media.text, video_stream_id))

        # Work out which blocks belong to the video side but not the surviving audio
        # side (a shared Markers block is reachable from both, so it must stay).
        blocks = fragment.toplevel_blocks()

        if master := blocks.containing(self.name).by_tag(Tag.MasterClip).first():
            video_clip_id = TimelapseXmlOps.master_clip_slot_ref(master.text, _VIDEO_SLOT)
            audio_clip_id = TimelapseXmlOps.master_clip_slot_ref(master.text, _AUDIO_SLOT)
        else:
            video_clip_id = None
            audio_clip_id = None

        video_clip = blocks.by_id(Tag.VideoClip, video_clip_id)
        audio_clip = blocks.by_id(Tag.AudioClip, audio_clip_id)

        video_side = {video_stream_id}
        if video_clip_id:
            video_side.add(video_clip_id)
        if video_clip:
            video_side |= TimelapseXmlOps.reference_ids(video_clip.text)

        if audio_clip:
            audio_side = TimelapseXmlOps.reference_ids(audio_clip.text)
        else:
            audio_side = set()

        removed = video_side - audio_side

        fragment.remove_blocks_by_positions([block.span for block in blocks if block.id in removed])

        # Drop the emptied video slot from the MasterClip and promote the audio to slot 0.
        if video_clip_id and audio_clip_id:
            if master := fragment.toplevel_blocks().containing(self.name).by_tag(Tag.MasterClip).first():
                fragment.replace_range(*master.span, TimelapseXmlOps.promote_audio_to_first_slot(master.text, video_clip_id, audio_clip_id))

        return fragment.text


class VideoSound(Sound):
    """A sound file that carries both video and audio tracks (mp4).

    The template's sound is already an mp4, so no structural changes needed.
    """

    def __init__(self, path: Path) -> None:
        self.__path = path

    @property
    def path(self) -> Path:
        return self.__path

    def adapt(self, section: str) -> str:
        return self.rename(section)
