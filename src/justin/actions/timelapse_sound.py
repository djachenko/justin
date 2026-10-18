import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TypeVar

from justin.actions.timelapse_model import AudioClip, Document, MasterClip, Media, PremiereObject, VideoClip
from justin.actions.timelapse_template import TimelapseTemplate
from justin.actions.timelapse_ticks import seconds_to_ticks
from justin.actions.timelapse_xml import Xml

# Formats that carry audio only — no picture. The template's sound is an mp4
# (which has a video part), so clones of these need that video part stripped.
AUDIO_ONLY_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".aac",
    ".m4a",
    ".flac",
    ".ogg",
    ".aiff",
}
VIDEO_AS_AUDIO_EXTENSIONS = {
    ".mp4",
}

_T = TypeVar("_T", bound=PremiereObject)


@dataclass(frozen=True)
class Sound(ABC):
    """A sound file from the timelapse folder, and how to turn the template's sound into it.

    Subclasses differ by format: how much of the template's mp4 structure the file
    keeps. Pick one with :meth:`from_path`.
    """

    path: Path

    @property
    def name(self) -> str:
        """The file name with extension — what the project calls the clip and the media."""
        return self.path.name

    @property
    def stem(self) -> str:
        """The file name without extension — accepted as a shorthand for ``--timeline-sound``."""
        return self.path.stem

    @cached_property
    def duration_ticks(self) -> int:
        """How long this sound plays, in Premiere ticks (measured by ffprobe once, then cached)."""
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(self.path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return seconds_to_ticks(float(probe.stdout.strip()))

    @abstractmethod
    def adapt(self, section: str) -> str:
        """Turn a copy of the template's sound section into this sound's section.

        ``section`` is the raw text of the template sound's blocks. The result
        describes this sound instead: the placeholder file name replaced by this
        sound's name, and the structure fitted to its format (an audio-only file
        loses the video part the mp4 template carries).

        Ids are left as the template's — the caller assigns fresh ones when it
        splices the section into the project. Subclasses build this out of
        ``replace_name``.
        """
        pass

    def replace_name(self, section: str) -> str:
        """Swap the template's placeholder sound name for this sound's real filename."""
        return section.replace(TimelapseTemplate.SOUND_NAME, self.name)

    @classmethod
    def from_path(cls, path: Path) -> "Sound":
        """The ``Sound`` subclass matching the file's extension.

        Returns ``Sound``, not ``Self``: the subclass is chosen by the extension, not
        by the class it is called on. Raises ``ValueError`` for an unsupported format.
        """
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
        section = self.replace_name(section)
        fragment = Xml(section)
        media = self._own(Document(fragment.toplevel_blocks()), Media)

        if media is None:
            return section

        video_stream = media.video_stream

        if video_stream is None:
            return section  # no video part — already audio-only, nothing to do

        video_stream_id = video_stream.block.id

        fragment.replace_range(*media.without_video_stream(video_stream))

        # Work out which blocks belong to the video side but not the surviving audio
        # side (a shared Markers block is reachable from both, so it must stay).
        document = Document(fragment.toplevel_blocks())
        master = self._own(document, MasterClip)

        if master is not None:
            halves = master.clips
        else:
            halves = []

        video_clip = next((clip for clip in halves if isinstance(clip, VideoClip)), None)
        audio_clip = next((clip for clip in halves if isinstance(clip, AudioClip)), None)

        video_side = {
            video_stream_id,
        }

        if video_clip:
            video_side.add(video_clip.block.id)
            video_side |= video_clip.refs

        if audio_clip:
            audio_side = audio_clip.refs
        else:
            audio_side = set()

        removed = video_side - audio_side

        fragment.remove_blocks_by_positions([obj.block.span for obj in document if obj.block.id in removed])

        # Drop the emptied video slot from the MasterClip and promote the audio to slot 0.
        if video_clip and audio_clip and (master := self._own(Document(fragment.toplevel_blocks()), MasterClip)):
            fragment.replace_range(*master.without_video_half(video_clip, audio_clip))

        return fragment.text

    def _own(self, document: Document, model_class: type[_T]) -> _T | None:
        """The one object of that class that belongs to this sound — the section may
        also carry blocks built from other placeholders, so match on the filename."""
        return next((obj for obj in document.of_type(model_class) if self.name in obj.block.text), None)


class VideoSound(Sound):
    """A sound file that carries both video and audio tracks (mp4).

    The template's sound is already an mp4, so no structural changes needed.
    """

    def adapt(self, section: str) -> str:
        """Rename to this sound's file; the mp4 template's structure already fits."""
        return self.replace_name(section)
