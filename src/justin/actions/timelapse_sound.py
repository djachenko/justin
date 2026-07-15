import re
from abc import ABC, abstractmethod
from pathlib import Path

from justin.actions.timelapse_tags import Tag
from justin.actions.timelapse_xml import Xml

# Formats that carry audio only — no picture. The template's sound is an mp4
# (which has a video part), so clones of these need that video part stripped.
AUDIO_ONLY_EXTENSIONS = {".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg", ".aiff"}
VIDEO_AS_AUDIO_EXTENSIONS = {".mp4"}


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
    def adapt(self, xml: Xml) -> None:
        """Adapt the XML to match this sound's structure."""
        ...

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
    attached. ``adapt`` strips that video half out of the XML.
    """

    def __init__(self, path: Path) -> None:
        self.__path = path

    @property
    def path(self) -> Path:
        return self.__path

    def adapt(self, xml: Xml) -> None:
        """Strip the video half that the template's mp4 sound carries.

        The template's sound is an mp4, so it has both a video part and an
        audio part. A plain audio file has no video, so we remove:
          * the video-stream pointer from the Media chunk and the stream block itself;
          * the VideoClip and the little chunks that hang off it (its markers,
            its video source) — but only the ones the surviving AudioClip doesn't
            also need (markers can be shared);
          * the VideoClip entry in the MasterClip's clip list, and the AudioClip
            moves up from slot 1 to slot 0.
        """
        blocks = xml.toplevel_blocks()

        sound_media = next(
            (b for b in blocks if self.name in b.text and b.tag == Tag.Media),
            None,
        )
        if sound_media is None:
            return
        video_stream_ref = re.search(r'<VideoStream ObjectRef="(\d+)"/>', sound_media.text)
        if video_stream_ref is None:
            return  # no video part — already audio-only, nothing to do
        video_stream_id = video_stream_ref.group(1)

        media_without_video = sound_media.text.replace(
            f'\t\t<VideoStream ObjectRef="{video_stream_id}"/>\n', ''
        )
        xml.replace_range(sound_media.start, sound_media.end, media_without_video)
        blocks = xml.toplevel_blocks()

        # Collect which sub-ids belong to the video side vs. the audio side of MasterClip.
        master_clip = next(
            (b for b in blocks if self.name in b.text and b.tag == Tag.MasterClip),
            None,
        )
        video_clip_id: str | None = None
        video_clip_sub_ids: set[str] = set()
        audio_clip_sub_ids: set[str] = set()
        if master_clip:
            if video_clip_ref := re.search(r'<Clip Index="0" ObjectRef="(\d+)"/>', master_clip.text):
                video_clip_id = video_clip_ref.group(1)
                video_clip = next(
                    (b for b in blocks if b.tag == Tag.VideoClip and f'ObjectID="{video_clip_id}"' in b.header),
                    None,
                )
                if video_clip:
                    video_clip_sub_ids = set(re.findall(r'ObjectRef="(\d+)"', video_clip.text))
            if audio_clip_ref := re.search(r'<Clip Index="1" ObjectRef="(\d+)"/>', master_clip.text):
                audio_clip = next(
                    (b for b in blocks if b.tag == Tag.AudioClip and f'ObjectID="{audio_clip_ref.group(1)}"' in b.header),
                    None,
                )
                if audio_clip:
                    audio_clip_sub_ids = set(re.findall(r'ObjectRef="(\d+)"', audio_clip.text))

        video_side_ids = {video_stream_id} | video_clip_sub_ids
        if video_clip_id:
            video_side_ids.add(video_clip_id)
        ids_to_remove = video_side_ids - audio_clip_sub_ids
        to_delete = [
            b.span for b in blocks
            if any(f'ObjectID="{bid}"' in b.header for bid in ids_to_remove)
        ]
        xml.remove_blocks_by_positions(to_delete)

        # Drop the VideoClip entry from MasterClip and renumber AudioClip to slot 0.
        if video_clip_id and master_clip:
            blocks = xml.toplevel_blocks()
            master_clip = next(
                (b for b in blocks if self.name in b.text and b.tag == Tag.MasterClip),
                None,
            )
            if master_clip:
                clips_list = master_clip.text
                clips_list = clips_list.replace(
                    f'\t\t<Clip Index="0" ObjectRef="{video_clip_id}"/>\n', ''
                )
                clips_list = re.sub(
                    r'<Clip Index="1" ObjectRef=', '<Clip Index="0" ObjectRef=',
                    clips_list, count=1,
                )
                xml.replace_range(master_clip.start, master_clip.end, clips_list)


class VideoSound(Sound):
    """A sound file that carries both video and audio tracks (mp4).

    The template's sound is already an mp4, so no structural changes needed.
    """

    def __init__(self, path: Path) -> None:
        self.__path = path

    @property
    def path(self) -> Path:
        return self.__path

    def adapt(self, xml: Xml) -> None:
        pass
