"""
Make a Premiere Pro project file (``.prproj``) for a timelapse.

What a ``.prproj`` actually is: a text file (XML) that's been zipped. Inside,
the whole project is described as a long list of little chunks — one chunk per
"thing" in the project: a clip, a sound, a track, and so on. Each chunk carries
an id, and chunks point at each other by those ids (like "this timeline slot
plays clip #56"). We call each chunk a *block*.

Writing such a file correctly from scratch is hopeless — there are hundreds of
interlocking chunks. So instead we cheat: someone built one good timelapse
project by hand in Premiere and saved it (the "wolfday" template,
``step_12_sound_in_timeline.prproj`` — an image sequence + a cover frame + one
sound on the timeline, 10 fps). We open that file's text and carefully edit it
to describe the timelapse we actually want:

  * swap in the right folder paths, frame count, and durations (``_substitute_*``);
  * make the template's sound match the real sound — including stripping the
    video part for audio-only files like mp3 (``_adapt_sound_to_audio_only``);
  * copy the sound's chunks once per extra sound (``_add_extra_sounds``);
  * put chosen sounds on the timeline, or leave them only in the project's clip
    list (``_layout_sounds_in_timeline`` / ``_remove_sounds_from_timeline``);
  * throw away the cover frame or the sound entirely if the timelapse has none.

Every block carries ids so other blocks can refer to it. There are two flavours
of id, and the difference bites you if you ignore it:

  * ``ObjectID`` / ``ObjectRef`` — plain small numbers. A number is unique only
    among blocks of the *same kind*, so number 56 can name several different
    blocks of different kinds. Don't assume a number is globally unique.
  * ``ObjectUID`` / ``ObjectURef`` — long random codes (uuids), unique everywhere.

We do almost all the editing one block at a time: ``parse_toplevel_blocks``
finds where each block starts and ends in the raw text, and we cut blocks out or
splice them back in with ordinary string slicing.
"""

import re
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

from justin.actions.timelapse_xml import Xml

# Premiere measures time in "ticks". This many ticks make one second.
PREMIERE_TIMEBASE = 254_016_000_000

# The exact values that appear in the wolfday template, so we can find them and
# replace them with the target's values. The template is: an image sequence +
# a cover frame + one mp4 sound, 106 frames at 10 fps.
_WD_TIMELAPSE_DIR = "/Users/justin/photos/stages/stage1.filter/26.04.17.wolfday/timelapse"
_WD_FIRST_FRAME   = "26.04.17.wolfday_0001.jpg"
_WD_SOUND_NAME    = "snejnye_volki.mp4"
_WD_PHOTOSET      = "26.04.17.wolfday"
_WD_FPS_TICKS     = 25401600000    # length of one frame at 10 fps = one second / 10
_WD_N_FRAMES      = 106
_WD_FRAMES_DUR    = _WD_N_FRAMES * _WD_FPS_TICKS          # total length of the frames
_WD_SEQ_DUR       = (_WD_N_FRAMES + 1) * _WD_FPS_TICKS    # frames plus the extra cover frame

_TEMPLATE_PATH = (
    Path(__file__).parent.parent
    / "resources"
    / "timelapse_templates"
    / "step_12_sound_in_timeline.prproj"
)

_AUDIO_EXTS =      {".mp3", ".mp4", ".wav", ".aac", ".m4a", ".flac", ".ogg"}
# Formats that carry sound only, no picture. The template's sound is an mp4
# (which has a video part), so for these we have to remove that video part —
# see _adapt_sound_to_audio_only.
_AUDIO_ONLY_EXTS = {".mp3",         ".wav", ".aac", ".m4a", ".flac", ".ogg", ".aiff"}


@dataclass
class TimelapseSettings:
    name: str
    timelapse_dir: Path
    cover: Path | None
    sounds: list[Path]
    fps: float = 10.0
    # Which sounds should sit on the timeline. Anything not listed here stays
    # only in the project's clip list. Empty means: nothing on the timeline.
    timeline_sounds: list[str] = field(default_factory=list)

    @property
    def timeline_sound_paths(self) -> list[Path]:
        """The chosen timeline sounds, in the same order as ``sounds``.

        You can name a sound by its full filename or just its stem, so both
        "teoretiki.mp3" and "teoretiki" pick the same file.
        """
        return [
            s for s in self.sounds
            if s.name in self.timeline_sounds or s.stem in self.timeline_sounds
        ]


def from_timelapse_dir(
    timelapse_dir: Path, fps: float = 10.0, timeline_sounds: list[str] | None = None,
) -> TimelapseSettings:
    timelapse_dir = timelapse_dir.resolve()
    frames_dir = timelapse_dir / "frames"

    if not frames_dir.exists() or not any(frames_dir.glob("*.jpg")):
        raise ValueError(f"No frames in {frames_dir}")

    cover_path = timelapse_dir / "cover.jpg"

    cover: Path | None = None
    if cover_path.exists():
        cover = cover_path

    sound_dir = timelapse_dir / "sound"
    sounds: list[Path] = []
    if sound_dir.exists():
        sounds = sorted(
            f for f in sound_dir.iterdir()
            if f.is_file() and f.suffix.lower() in _AUDIO_EXTS
        )

    return TimelapseSettings(
        name=timelapse_dir.parent.name,
        timelapse_dir=timelapse_dir,
        cover=cover,
        sounds=sounds,
        fps=fps,
        timeline_sounds=list(timeline_sounds or []),
    )


def _count_frames(frames_dir: Path) -> int:
    return len(list(frames_dir.glob("*.jpg")) + list(frames_dir.glob("*.jpeg")))


def _first_frame(frames_dir: Path) -> str:
    frames = sorted(frames_dir.glob("*.jpg")) + sorted(frames_dir.glob("*.jpeg"))

    if not frames:
        raise ValueError(f"No JPG files in {frames_dir}")

    return frames[0].name


class Block(NamedTuple):
    """One chunk of the project, and where it sits in the raw text.

    ``text`` is the chunk's full ``<Tag ...>...</Tag>`` snippet. ``start`` and
    ``end`` are where that snippet begins and ends in the whole file, so we can
    cut it out or drop it back in by slicing the string at those positions.
    """
    start: int
    end: int
    tag: str
    text: str


def parse_toplevel_blocks(xml: str) -> list[Block]:
    return Xml(xml).toplevel_blocks()


def _remove_blocks_by_positions(xml: str, positions: list[tuple[int, int]]) -> str:
    # Cut from the end backwards, so cutting one chunk doesn't shift the
    # positions of the chunks we haven't cut yet.
    for start, end in sorted(positions, reverse=True):
        xml = xml[:start] + xml[end:]

    return xml


def _blocks_containing(blocks: list[Block], text: str) -> list[Block]:
    return [block for block in blocks if text in block.text]


def remove_dangling_refs(xml: str) -> str:
    """
    Clean up references that now point at nothing.

    When we delete a chunk (say the cover, or a sound), other chunks may still
    hold a reference to it — a pointer to an id that no longer exists. Premiere
    won't open a project with such broken pointers. This walks the whole project
    and removes every chunk left holding a broken pointer, then repeats, because
    removing one chunk can break another's pointer in turn. It stops once a full
    pass finds nothing more to remove.

    Two kinds of pointer are followed:
      * uuid pointers (ObjectURef) from Media / VideoClip / AudioClip / MasterClip;
      * number pointers (ObjectRef) from SubClip / Source / Content.
    It also tidies the two lists that name clips by pointer — the project's clip
    list (``<Items>``) and each track's clip list (``<TrackItems>``).
    """
    for _ in range(10):
        # Может сюда отдельно добавить эгекс для уида? 
        live_uids = set(re.findall(r'ObjectUID="([^"]+)"', xml))
        live_ids = set(re.findall(r'ObjectID="(\d+)"', xml))

        # In the project's clip list, drop any entry that points at a gone clip.
        def prune_panel_items(items_block: re.Match) -> str:
            def keep(item: re.Match) -> str:
                uref = re.search(r'ObjectURef="([^"]+)"', item.group(0))

                if uref and uref.group(1) not in live_uids:
                    return ''

                return item.group(0)

            # The space after "<Item " matters: without it the pattern would also
            # match "<Items " and eat the list's own opening tag.
            return re.sub(r'[^\S\n]*<Item [^/]*/>\n', keep, items_block.group(0))

        xml = re.sub(r'<Items Version="\d+">.*?</Items>', prune_panel_items, xml, flags=re.DOTALL)

        # In each track's clip list, drop entries pointing at a gone clip, then
        # renumber what's left so the indexes stay 0, 1, 2, ...
        def prune_track_items(track_items_block: re.Match) -> str:
            def keep(item: re.Match) -> str:
                ref = re.search(r'ObjectRef="(\d+)"', item.group(0))
                if ref and ref.group(1) not in live_ids:
                    return ''
                return item.group(0)
            # Same trap as above: "<TrackItem " needs the space so it doesn't
            # match the list tag "<TrackItems ".
            block = re.sub(r'[^\S\n]*<TrackItem [^/]*/>\n', keep, track_items_block.group(0))
            surviving = list(re.finditer(r'<TrackItem Index="\d+" ObjectRef="(\d+)"/>', block))
            for new_index, item in enumerate(surviving):
                renumbered = f'<TrackItem Index="{new_index}" ObjectRef="{item.group(1)}"/>'
                block = block.replace(item.group(0), renumbered, 1)
            return block

        xml = re.sub(r'<TrackItems Version="\d+">.*?</TrackItems>', prune_track_items, xml, flags=re.DOTALL)

        live_uids = set(re.findall(r'ObjectUID="([^"]+)"', xml))
        live_ids = set(re.findall(r'ObjectID="(\d+)"', xml))
        to_delete: list[tuple[int, int]] = []
        for block in parse_toplevel_blocks(xml):
            uuid_refs = re.findall(r'<(?:Media|VideoClip|AudioClip|MasterClip) ObjectURef="([^"]+)"', block.text)
            if any(ref not in live_uids for ref in uuid_refs):
                to_delete.append((block.start, block.end))
                continue
            # A clip points at its media by number. When we delete a media chunk
            # by filename, the clip that pointed to it (VideoClip / AudioClip /
            # SecondaryContent) is now broken, so it goes too — and so on up the
            # chain on the next pass.
            numeric_refs = re.findall(r'<(?:SubClip|Source|Content) ObjectRef="(\d+)"', block.text)
            if any(ref not in live_ids for ref in numeric_refs):
                to_delete.append((block.start, block.end))

        if not to_delete:
            break
        xml = _remove_blocks_by_positions(xml, to_delete)

    return xml


# The kinds of chunk that together make up one clip (its picture/sound data and
# all its little helpers) — as opposed to the shared scaffolding of the project
# (the sequence, the tracks, the project root). When we walk a clip's pointers
# to gather all its chunks, we stay inside this set so we never wander off into
# the shared scaffolding and start dragging that around.
_CLIP_MEDIA_TYPES = {
    "ClipProjectItem", "MasterClip", "AudioClip", "VideoClip", "SubClip",
    "Media", "AudioStream", "VideoStream", "AudioMediaSource", "VideoMediaSource",
    "Markers", "AudioComponentChain", "ClipLoggingInfo",
    "SecondaryContent", "ClipChannelSerializer",
    "ClipChannelGroupVectorSerializer", "ClipChannelVectorSerializer",
}


def _collect_sound_closure(blocks: list[Block], entry_idxs: list[int]) -> list[int]:
    """
    Gather every chunk that belongs to a clip, starting from a few known chunks.

    A clip is not one chunk — it's a little cluster of them (the audio data, its
    markers, its channel info, ...) wired together by pointers. Only a couple of
    those chunks actually mention the filename; the rest you can only reach by
    following the pointers. So we start from the chunks that name the file
    (``entry_idxs``) and keep hopping along pointers until we've collected the
    whole cluster.

    One wrinkle: a pointer's tag doesn't always tell you the kind of chunk it
    points at (e.g. ``<Clip ObjectRef="56"/>`` might mean a VideoClip or an
    AudioClip). So for number pointers we accept any clip-kind chunk carrying
    that number; uuid pointers are unambiguous and looked up directly.
    """
    media_idxs_by_id: dict[str, list[int]] = {}
    idx_by_uid: dict[str, int] = {}

    for idx, block in enumerate(blocks):
        own_id = re.search(r'ObjectID="(\d+)"', block.text[:120])

        if own_id and block.tag in _CLIP_MEDIA_TYPES:
            media_idxs_by_id.setdefault(own_id.group(1), []).append(idx)

        own_uid = re.search(r'ObjectUID="([^"]+)"', block.text[:120])

        if own_uid:
            idx_by_uid[own_uid.group(1)] = idx

    reached = set(entry_idxs)
    frontier = list(entry_idxs)
    while frontier:
        block = blocks[frontier.pop()]
        for ref in re.finditer(r'ObjectRef="(\d+)"', block.text):
            for target in media_idxs_by_id.get(ref.group(1), []):
                if target not in reached:
                    reached.add(target)
                    frontier.append(target)
        for uref in re.finditer(r'ObjectURef="([^"]+)"', block.text):
            target = idx_by_uid.get(uref.group(1))
            if target is not None and blocks[target].tag in _CLIP_MEDIA_TYPES and target not in reached:
                reached.add(target)
                frontier.append(target)
    return sorted(reached)


def _probe_duration_ticks(path: Path) -> int:
    """Ask ffprobe how long a media file is, and give it back in Premiere ticks."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return int(float(probe.stdout.strip()) * PREMIERE_TIMEBASE)


def _clone_sound_blocks(blocks: list[Block], old_name: str, new_name: str, id_offset: int) -> str:
    """
    Make an independent copy of one sound's chunks, renamed for a new file.

    A copy has to be fully independent — it must not accidentally share an id
    with the original or with another copy, or Premiere gets confused. So we
    give the copy fresh identities:
      * every plain-number id is bumped by ``id_offset`` (picked bigger than any
        id already in use, so the bumped numbers can't clash);
      * every uuid identity (ObjectUID / ObjectURef, and the ``<ID>`` codes) is
        replaced with a brand-new uuid.

    What we must NOT touch is ClassID (and ESP.PresetGuid). Those look like uuids
    too, but they aren't identities — they say *what kind* of chunk this is, and
    every chunk of a kind shares the same one. Change those and Premiere no
    longer recognises the chunk's type and silently refuses to open the file.
    (This was the bug that made multi-sound projects fail to open.)
    """
    combined = ''.join(block.text for block in blocks)

    numeric_ids = sorted(set(re.findall(r'ObjectID="(\d+)"', combined)), key=int)
    id_remap = {old: str(int(old) + id_offset) for old in numeric_ids}

    identity_uids = set(re.findall(r'Object(?:UID|URef)="([0-9a-f-]{36})"', combined))
    identity_uids |= set(re.findall(r'<ID>([0-9a-f-]{36})</ID>', combined))
    uid_remap = {old: str(uuid.uuid4()) for old in identity_uids}

    clone = combined.replace(old_name, new_name)
    for old_id, new_id in id_remap.items():
        clone = re.sub(rf'((?:ObjectID|ObjectRef)="){re.escape(old_id)}"', rf'\g<1>{new_id}"', clone)
    for old_uid, new_uid in uid_remap.items():
        clone = clone.replace(old_uid, new_uid)
    return clone


@dataclass(frozen=True)
class TimelapseSchema:

    def __call__(self, output_path: Path, settings: TimelapseSettings) -> Path:
        timeline_sounds = settings.timeline_sound_paths

        frames_dir = settings.timelapse_dir / "frames"
        n_frames = _count_frames(frames_dir)
        first_frame = _first_frame(frames_dir)

        fps_ticks = int(PREMIERE_TIMEBASE / settings.fps)
        frames_dur = n_frames * fps_ticks

        # The cover, if there is one, is shown as one extra frame before the
        # sequence proper, so it adds one frame's worth of length.
        n_seq_frames = n_frames

        if settings.cover:
            n_seq_frames += 1

        seq_dur = n_seq_frames * fps_ticks

        xml_obj = Xml.from_prproj(_TEMPLATE_PATH)
        xml = xml_obj.xml

        xml = self._substitute_paths(xml, settings, first_frame)
        xml = self._substitute_ticks(xml, fps_ticks, frames_dur, seq_dur)
        xml = self._clear_audio_caches(xml)

        # А получится ли здесь не жонглировать вот этими количествами звуков, а просто добавлять, типа снести все текущие звуки и новые добавить?
        if not settings.sounds:
            xml = self._remove_sound(xml)
        else:
            # Point the template's one sound at our first real sound...
            first_sound_name = settings.sounds[0].name

            if first_sound_name != _WD_SOUND_NAME:
                xml = xml.replace(f"./sound/{_WD_SOUND_NAME}", f"./sound/{first_sound_name}")
                xml = xml.replace(_WD_SOUND_NAME, first_sound_name)

            if Path(first_sound_name).suffix.lower() in _AUDIO_ONLY_EXTS:
                xml = self._adapt_sound_to_audio_only(xml, first_sound_name)

            # ...then copy in a fresh version for each of the other sounds.
            if len(settings.sounds) > 1:
                xml = self._add_extra_sounds(xml, settings.sounds, bool(timeline_sounds))

            # А если здесь просто снести все с таймлайна безусловно и добавить на таймлайн просто все нужные, типа не парясь где какие оставить, все убираем и нужные добавляем.

            # At this point every sound exists in the project's clip list. Now
            # take off the timeline the ones we don't want there, and line up the
            # ones we keep so they play back-to-back.
            keep_on_timeline = {sound.name for sound in timeline_sounds}
            xml = self._remove_sounds_from_timeline(xml, keep_on_timeline)


            if timeline_sounds:
                xml = self._layout_sounds_in_timeline(xml, timeline_sounds)

        if not settings.cover:
            xml = self._remove_cover(xml, fps_ticks, frames_dur, seq_dur)

        xml = remove_dangling_refs(xml)

        xml_obj.xml = xml
        xml_obj.to_prproj(output_path)

        return output_path

    @staticmethod
    def _substitute_paths(xml: str, settings: TimelapseSettings, first_frame: str) -> str:
        # Swap every mention of the template's folders/names for the target's.
        xml = xml.replace(_WD_TIMELAPSE_DIR, str(settings.timelapse_dir))
        xml = xml.replace(f"./frames/{_WD_FIRST_FRAME}", f"./frames/{first_frame}")
        xml = xml.replace(_WD_FIRST_FRAME, first_frame)
        xml = xml.replace(_WD_PHOTOSET, settings.name)
        return xml

    @staticmethod
    def _substitute_ticks(xml: str, fps_ticks: int, frames_dur: int, seq_dur: int) -> str:
        # Frame rate: how long one frame lasts.
        # Что значат эти значения?
        # Типа тут в целом задается фреймрейт для всего проекта или что?
        for tag in ("OveriddenFrameRate", "FrameRate"):
            xml = xml.replace(f"<{tag}>{_WD_FPS_TICKS}</{tag}>", f"<{tag}>{fps_ticks}</{tag}>")

        xml = xml.replace(f"<End>{_WD_FPS_TICKS}</End>", f"<End>{fps_ticks}</End>")          # where the cover frame ends
        xml = xml.replace(f"<Start>{_WD_FPS_TICKS}</Start>", f"<Start>{fps_ticks}</Start>")  # where the frames clip starts

        # Total lengths.
        xml = xml.replace(f"<End>{_WD_SEQ_DUR}</End>", f"<End>{seq_dur}</End>")  # where the frames clip ends (after the cover)

        # Что значат эти значения?
        for tag in ("OriginalDuration", "OutPoint", "MZ.WorkOutPoint"):
            xml = xml.replace(f"<{tag}>{_WD_FRAMES_DUR}</{tag}>", f"<{tag}>{frames_dur}</{tag}>")

        return xml

    @staticmethod
    def _clear_audio_caches(xml: str) -> str:
        # The template remembers where it cached the waveform/peaks for its own
        # sound, on the machine it was made on. Blank those paths so Premiere
        # rebuilds the cache for our sound instead of trusting stale files.
        xml = re.sub(r'<ConformedAudioPath>[^<]+</ConformedAudioPath>', '<ConformedAudioPath></ConformedAudioPath>', xml)
        xml = re.sub(r'<PeakFilePath>[^<]+</PeakFilePath>', '<PeakFilePath></PeakFilePath>', xml)
        return xml

    @staticmethod
    def _adapt_sound_to_audio_only(xml: str, sound_name: str) -> str:
        """
        Turn the template's mp4 sound into a plain audio-only sound (mp3, wav...).

        The template's sound is an mp4, so it carries a video part as well as an
        audio part. A plain audio file has no video, so we have to remove that
        video half of the cluster:

          * take the video-stream pointer out of the Media chunk, and delete the
            top-level video-stream chunk;
          * delete the VideoClip and the little chunks that hang off it (its
            markers, its video source);
          * fix the MasterClip's clip list — remove the VideoClip entry and move
            the AudioClip up to slot 0.

        Careful bit: a markers chunk can be *shared* by the VideoClip and the
        AudioClip. We must never delete a chunk the surviving AudioClip still
        needs, even if it also belonged to the video side.
        """
        blocks = parse_toplevel_blocks(xml)

        # The sound's Media chunk is where the video-stream pointer lives.
        sound_media = next(
            (b for b in _blocks_containing(blocks, sound_name) if b.tag == "Media"),
            None,
        )
        if sound_media is None:
            return xml
        video_stream_ref = re.search(r'<VideoStream ObjectRef="(\d+)"/>', sound_media.text)
        if video_stream_ref is None:
            return xml  # no video part — already an audio-only sound, nothing to do
        video_stream_id = video_stream_ref.group(1)

        # Remove the video-stream pointer from the Media chunk.
        media_without_video = sound_media.text.replace(f'\t\t<VideoStream ObjectRef="{video_stream_id}"/>\n', '')
        xml = xml[:sound_media.start] + media_without_video + xml[sound_media.end:]
        blocks = parse_toplevel_blocks(xml)

        # The MasterClip lists its clips: slot 0 is the VideoClip, slot 1 the AudioClip.
        master_clip = next(
            (b for b in _blocks_containing(blocks, sound_name) if b.tag == "MasterClip"),
            None,
        )
        video_clip_id: str | None = None
        video_clip_sub_ids: set[str] = set()
        audio_clip_sub_ids: set[str] = set()
        if master_clip:
            video_clip_ref = re.search(r'<Clip Index="0" ObjectRef="(\d+)"/>', master_clip.text)
            if video_clip_ref:
                video_clip_id = video_clip_ref.group(1)
                video_clip = next(
                    (b for b in blocks if b.tag == "VideoClip" and f'ObjectID="{video_clip_id}"' in b.text[:80]),
                    None,
                )
                if video_clip:
                    video_clip_sub_ids = set(re.findall(r'ObjectRef="(\d+)"', video_clip.text))
            # Note which chunks the AudioClip still points at, so we keep them —
            # the markers chunk may be shared between the video and audio sides.
            audio_clip_ref = re.search(r'<Clip Index="1" ObjectRef="(\d+)"/>', master_clip.text)
            if audio_clip_ref:
                audio_clip = next(
                    (b for b in blocks if b.tag == "AudioClip" and f'ObjectID="{audio_clip_ref.group(1)}"' in b.text[:80]),
                    None,
                )
                if audio_clip:
                    audio_clip_sub_ids = set(re.findall(r'ObjectRef="(\d+)"', audio_clip.text))

        # Delete the video-side chunks — but not any the audio side still needs.
        video_side_ids = {video_stream_id} | video_clip_sub_ids
        if video_clip_id:
            video_side_ids.add(video_clip_id)
        ids_to_remove = video_side_ids - audio_clip_sub_ids
        to_delete = [
            (b.start, b.end) for b in blocks
            if any(f'ObjectID="{block_id}"' in b.text[:80] for block_id in ids_to_remove)
        ]
        xml = _remove_blocks_by_positions(xml, to_delete)

        # Fix up the MasterClip's clip list: drop the VideoClip entry (slot 0)
        # and move the AudioClip from slot 1 to slot 0.
        if video_clip_id and master_clip:
            blocks = parse_toplevel_blocks(xml)
            master_clip = next(
                (b for b in _blocks_containing(blocks, sound_name) if b.tag == "MasterClip"),
                None,
            )
            if master_clip:
                clips_list = master_clip.text
                clips_list = clips_list.replace(f'\t\t<Clip Index="0" ObjectRef="{video_clip_id}"/>\n', '')
                clips_list = re.sub(r'<Clip Index="1" ObjectRef=', '<Clip Index="0" ObjectRef=', clips_list, count=1)
                xml = xml[:master_clip.start] + clips_list + xml[master_clip.end:]

        return xml

    @staticmethod
    def _remove_sound(xml: str) -> str:
        """Remove the template's sound completely (this timelapse has none)."""
        blocks = parse_toplevel_blocks(xml)
        sound_blocks = _blocks_containing(blocks, _WD_SOUND_NAME)

        return _remove_blocks_by_positions(xml, [(b.start, b.end) for b in sound_blocks])

    # В чем прикол именно экстра саундс? Почему нельзя сделать... То есть есть какой-то первый саунд и к нему добавляются остальные, а почему нельзя просто взять и добавить все вместе? Типа убираем исходный и добавляем новые туда же.
    @staticmethod
    def _add_extra_sounds(xml: str, sounds: list[Path], timeline: bool = False) -> str:
        """
        Copy the extra sounds (everything after the first) into the project.

        The first sound already exists — it's the template's own sound, renamed.
        Each extra sound is a full independent copy of that sound's whole cluster
        of chunks (found by following the first sound's pointers) with fresh ids.

        If ``timeline`` is False the copies only appear in the project's clip
        list, ready to be dragged onto the timeline by hand. If it's True the
        copied cluster also includes the timeline slot, so each copy is placed on
        the audio track as well.
        """
        blocks = parse_toplevel_blocks(xml)
        first_name = sounds[0].name

        # индексы блоков с именем первого звука?
        entry = [i for i, block in enumerate(blocks) if first_name in block.text]

        if timeline:
            entry += [i for i, block in enumerate(blocks) if block.tag == "AudioClipTrackItem"]

        source_blocks = [blocks[i] for i in _collect_sound_closure(blocks, entry)]

        # Remember the first sound's timeline slot and clip-list entry — we'll
        # register each copy's own versions right next to them.
        first_track_item = next((b for b in source_blocks if b.tag == "AudioClipTrackItem"), None)
        first_track_item_id = None

        if first_track_item:
            first_track_item_id = re.search(r'ObjectID="(\d+)"', first_track_item.text).group(1)

        max_id = max(int(i) for i in re.findall(r'ObjectID="(\d+)"', xml))
        insert_pos = max(b.end for b in source_blocks)

        first_panel_item = next((b for b in source_blocks if b.tag == "ClipProjectItem"), None)
        first_panel_item_uid = None
        if first_panel_item:
            first_panel_item_uid = re.search(r'ObjectUID="([^"]+)"', first_panel_item.text).group(1)

        cloned_blocks = ""
        new_panel_item_uids: list[str] = []
        new_track_item_ids: list[str] = []
        for i, sound in enumerate(sounds[1:], start=1):
            # Bumping by (max_id + 1) * i keeps every copy's numbers clear of the
            # original's and of every other copy's.
            clone = _clone_sound_blocks(source_blocks, first_name, sound.name, (max_id + 1) * i)
            cloned_blocks += clone
            panel_item = re.search(r'<ClipProjectItem ObjectUID="([^"]+)"', clone)
            if panel_item:
                new_panel_item_uids.append(panel_item.group(1))
            track_item = re.search(r'<AudioClipTrackItem ObjectID="(\d+)"', clone)
            if track_item:
                new_track_item_ids.append(track_item.group(1))

        xml = xml[:insert_pos] + cloned_blocks + xml[insert_pos:]

        # Add the copies to the project's clip list, right after the original, so
        # they actually show up in the project panel.
        if first_panel_item_uid and new_panel_item_uids:
            original_item = re.search(rf'<Item Index="(\d+)" ObjectURef="{re.escape(first_panel_item_uid)}"', xml)
            if original_item:
                base_index = int(original_item.group(1))
                added_items = "".join(
                    f'\n\t\t\t\t<Item Index="{base_index + offset}" ObjectURef="{uid}"/>'
                    for offset, uid in enumerate(new_panel_item_uids, start=1)
                )
                xml = xml.replace(
                    f'<Item Index="{base_index}" ObjectURef="{first_panel_item_uid}"/>',
                    f'<Item Index="{base_index}" ObjectURef="{first_panel_item_uid}"/>{added_items}',
                )

        if timeline and new_track_item_ids and first_track_item_id:
            xml = TimelapseSchema._append_track_items(xml, first_track_item_id, new_track_item_ids)

        return xml

    @staticmethod
    def _layout_sounds_in_timeline(xml: str, sounds: list[Path]) -> str:
        """
        Line the timeline sounds up back-to-back at their real lengths.

        Each sound's real length comes from ffprobe. The first sound starts at 0,
        the next starts where it ended, and so on. For each sound we set two
        things: the timeline slot's start/end (where the clip sits on the track)
        and the clip's own end point (how much of the clip plays). Slots are
        matched to sounds by filename and handled in the order they appear.
        """
        durations = {sound.name: _probe_duration_ticks(sound) for sound in sounds}
        cursor = 0
        placed_ids: set[str] = set()
        while True:
            blocks = parse_toplevel_blocks(xml)
            block_text_by_id = {
                (b.tag, re.search(r'ObjectID="(\d+)"', b.text[:120]).group(1)): b.text
                for b in blocks if re.search(r'ObjectID="(\d+)"', b.text[:120])
            }
            # Find the next timeline slot we haven't placed yet whose sound we know.
            track_item = next(
                (b for b in blocks
                 if b.tag == "AudioClipTrackItem"
                 and re.search(r'ObjectID="(\d+)"', b.text[:120]).group(1) not in placed_ids
                 and TimelapseSchema._track_item_sound_name(b.text, block_text_by_id) in durations),
                None,
            )
            if track_item is None:
                break
            track_item_id = re.search(r'ObjectID="(\d+)"', track_item.text[:120]).group(1)
            sound_name = TimelapseSchema._track_item_sound_name(track_item.text, block_text_by_id)
            duration = durations[sound_name]
            end = cursor + duration

            # Set where the clip sits on the track. It always has an end; it only
            # gets a start once we're past 0 (the very first clip has no start
            # written out, matching how the template stores it).
            new_position = f'<End>{end}</End>'
            if cursor:
                new_position = f'<Start>{cursor}</Start>\n\t\t\t\t<End>{end}</End>'
            positioned = re.sub(
                r'(?:<Start>\d+</Start>\n\t+)?<End>\d+</End>', new_position, track_item.text, count=1,
            )
            xml = xml[:track_item.start] + positioned + xml[track_item.end:]

            # Set how much of the clip plays, via the AudioClip's end point. We
            # reach the AudioClip by following the slot's SubClip pointer. (Re-scan
            # the text first — the edit just above moved everything after it.)
            subclip_ref = re.search(r'<SubClip ObjectRef="(\d+)"', track_item.text)
            audio_clip_ref = None
            if subclip_ref:
                subclip_text = block_text_by_id[("SubClip", subclip_ref.group(1))]
                audio_clip_ref = re.search(r'<Clip ObjectRef="(\d+)"', subclip_text)
            if audio_clip_ref:
                audio_clip_text = block_text_by_id.get(("AudioClip", audio_clip_ref.group(1)))
                if audio_clip_text and "<OutPoint>" in audio_clip_text:
                    trimmed = re.sub(r'<OutPoint>\d+</OutPoint>', f'<OutPoint>{duration}</OutPoint>', audio_clip_text, count=1)
                    audio_clip = next(
                        (b for b in parse_toplevel_blocks(xml)
                         if b.tag == "AudioClip" and f'ObjectID="{audio_clip_ref.group(1)}"' in b.text[:120]),
                        None,
                    )
                    if audio_clip:
                        xml = xml[:audio_clip.start] + trimmed + xml[audio_clip.end:]

            placed_ids.add(track_item_id)
            cursor = end
        return xml

    @staticmethod
    def _track_item_sound_name(track_item_text: str, block_text_by_id: dict) -> str | None:
        """Which sound file a timeline slot plays (read off its SubClip's Name)."""
        subclip_ref = re.search(r'<SubClip ObjectRef="(\d+)"', track_item_text)
        if not subclip_ref:
            return None
        subclip = block_text_by_id.get(("SubClip", subclip_ref.group(1)))
        if not subclip:
            return None
        name = re.search(r'<Name>([^<]+)</Name>', subclip)
        if not name:
            return None
        return name.group(1)

    @staticmethod
    def _remove_sounds_from_timeline(xml: str, keep_names: set[str] = frozenset()) -> str:
        """
        Take sounds off the timeline while keeping them in the project's clip list.
        Any sound whose filename is in ``keep_names`` is left on the timeline.

        Taking a sound off the timeline means deleting its timeline slot *and* the
        few chunks that belong only to that slot (its own SubClip / AudioClip /
        components). "Belong only to it" is worked out as: the chunks reachable
        from the slots we're removing, minus the chunks reachable from the clip
        list and from the slots we're keeping. That way anything shared — like a
        markers chunk the clip-list copy also uses, or a chunk another kept sound
        needs — is left alone. Finally the removed slots are struck from the
        track's slot list.
        """
        blocks = parse_toplevel_blocks(xml)
        block_text_by_id = {
            (b.tag, re.search(r'ObjectID="(\d+)"', b.text[:120]).group(1)): b.text
            for b in blocks if re.search(r'ObjectID="(\d+)"', b.text[:120])
        }
        all_track_items = [i for i, b in enumerate(blocks) if b.tag == "AudioClipTrackItem"]
        dropped = [
            i for i in all_track_items
            if TimelapseSchema._track_item_sound_name(blocks[i].text, block_text_by_id) not in keep_names
        ]
        kept = [i for i in all_track_items if i not in dropped]
        if not dropped:
            return xml

        keep_entry = [i for i, b in enumerate(blocks) if b.tag == "ClipProjectItem"] + kept
        keep_closure = set(_collect_sound_closure(blocks, keep_entry))
        dropped_closure = set(_collect_sound_closure(blocks, dropped))
        to_remove = (dropped_closure - keep_closure) | set(dropped)

        dropped_ids = [re.search(r'ObjectID="(\d+)"', blocks[i].text[:120]).group(1) for i in dropped]
        xml = _remove_blocks_by_positions(xml, [(blocks[i].start, blocks[i].end) for i in to_remove])
        for track_item_id in dropped_ids:
            xml = re.sub(rf'[^\S\n]*<TrackItem Index="\d+" ObjectRef="{track_item_id}"/>\n', '', xml)
        return xml

    @staticmethod
    def _append_track_items(xml: str, anchor_id: str, track_item_ids: list[str]) -> str:
        """
        Add the given timeline slots to the audio track's slot list.

        There are several slot lists (one per track). We find the right one — the
        audio track's — by locating the list that already contains the first
        sound's slot (``anchor_id``), so we don't accidentally add to the video
        track's list.
        """
        def append_after_last(track_items_block: re.Match) -> str:
            listing = track_items_block.group(0)
            existing = list(re.finditer(r'<TrackItem Index="(\d+)" ObjectRef="\d+"/>', listing))
            last_index = int(existing[-1].group(1))
            added = "".join(
                f'\n\t\t\t\t\t<TrackItem Index="{last_index + offset}" ObjectRef="{track_item_id}"/>'
                for offset, track_item_id in enumerate(track_item_ids, start=1)
            )
            return listing.replace(existing[-1].group(0), existing[-1].group(0) + added, 1)

        return re.sub(
            rf'<TrackItems Version="\d+">(?:(?!</TrackItems>).)*?'
            rf'<TrackItem Index="\d+" ObjectRef="{anchor_id}"/>.*?</TrackItems>',
            append_after_last, xml, count=1, flags=re.DOTALL,
        )

    # Здесь нужно еще обработать кейс, когда кавер на таймлайне, но мы его удаляем и соответственно надо весь таймлайн сдвинуть влево.
    # Или это здесь уже обрабатывается что ли?
    @staticmethod
    def _remove_cover(xml: str, fps_ticks: int, frames_dur: int, seq_dur: int) -> str:
        """Remove the cover frame and slide the image sequence back to the start."""
        # Cut the cover's own media chunks (the ones that name cover.jpg). The
        # rest of the cover's cluster (its VideoClip, its timeline slot, its slot
        # list entry) then has nothing pointing to it, so remove_dangling_refs
        # sweeps it away for us.
        blocks = parse_toplevel_blocks(xml)
        cover_blocks = _blocks_containing(blocks, "cover.jpg")

        xml = _remove_blocks_by_positions(xml, [(b.start, b.end) for b in cover_blocks])
        xml = remove_dangling_refs(xml)

        # The frames clip used to sit one cover-frame in, from [fps_ticks → seq_dur].
        # With the cover gone it starts at the very beginning: [0 → frames_dur].
        xml = xml.replace(f"<Start>{fps_ticks}</Start>", "<Start>0</Start>")
        xml = xml.replace(f"<End>{seq_dur}</End>", f"<End>{frames_dur}</End>")

        return xml


def generate_prproj(
    timelapse_dir: Path, fps: float = 10.0, timeline_sounds: list[str] | None = None,
) -> Path:
    timelapse_dir = timelapse_dir.resolve()
    settings = from_timelapse_dir(timelapse_dir, fps, timeline_sounds)
    output_path = timelapse_dir / f"{settings.name}.prproj"

    # Don't clobber an existing project (it may have been edited by hand) — pick
    # the next free numbered name instead.
    if output_path.exists():
        i = 1
        while (candidate := timelapse_dir / f"{settings.name}_{i}.prproj").exists():
            i += 1
        output_path = candidate

    n_frames = _count_frames(timelapse_dir / "frames")
    frames_line = str(n_frames)
    if settings.cover:
        frames_line += " + cover"
    timeline_line = [s.name for s in settings.timeline_sound_paths] or "panel only"

    print(f"Photoset:  {settings.name}")
    print(f"Frames:    {frames_line}")
    print(f"Sounds:    {[s.name for s in settings.sounds]}")
    print(f"FPS:       {fps}")
    print(f"Timeline:  {timeline_line}")

    return TimelapseSchema()(output_path, settings)
