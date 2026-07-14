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
from dataclasses import dataclass, field
from pathlib import Path

from justin.actions.timelapse_sources import AUDIO_ONLY_EXTENSIONS, TimelapseSources
from justin.actions.timelapse_xml import (
    Xml,
    collect_sound_closure as _collect_sound_closure,
    clone_sound_blocks as _clone_sound_blocks,
)

# Premiere measures time in "ticks". This many ticks make one second.
PREMIERE_TIMEBASE = 254_016_000_000

_TEMPLATE_PATH = (
    Path(__file__).parent.parent
    / "resources"
    / "timelapse_templates"
    / "template.prproj"
)

# Placeholder strings baked into the template. Each substitute_* method swaps
# these out for the real values of the target timelapse.
_TMPL_FIRST_FRAME   = "TMPL_FIRST_FRAME.jpg"
_TMPL_PHOTOSET      = "TMPL_PHOTOSET"
_TMPL_SOUND_NAME    = "TMPL_SOUND.mp4"

# Numeric values baked into the template (106 frames at 10 fps + 1 cover frame).
_TMPL_FPS_TICKS  = int(PREMIERE_TIMEBASE / 10)
_TMPL_N_FRAMES   = 106
_TMPL_FRAMES_DUR = _TMPL_N_FRAMES * _TMPL_FPS_TICKS
_TMPL_SEQ_DUR    = (_TMPL_N_FRAMES + 1) * _TMPL_FPS_TICKS

# Formats that carry sound only, no picture. The template's sound is an mp4
# (which has a video part), so for these we have to remove that video part —
# see _adapt_sound_to_audio_only.
_AUDIO_ONLY_EXTS = AUDIO_ONLY_EXTENSIONS


@dataclass
class TimelapseSettings:
    sources: TimelapseSources
    fps: float = 10.0
    # Which sounds should sit on the timeline. Anything not listed here stays
    # only in the project's clip list. Empty means: nothing on the timeline.
    timeline_sounds: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.sources.name

    @property
    def timelapse_dir(self) -> Path:
        return self.sources.folder

    @property
    def cover(self) -> Path | None:
        return self.sources.cover

    @property
    def sounds(self) -> list[Path]:
        return self.sources.sounds or []

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
    sources = TimelapseSources.from_folder(timelapse_dir.parent.name, timelapse_dir)
    return TimelapseSettings(sources=sources, fps=fps, timeline_sounds=list(timeline_sounds or []))



def _probe_duration_ticks(path: Path) -> int:
    """Ask ffprobe how long a media file is, and give it back in Premiere ticks."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )

    return int(float(probe.stdout.strip()) * PREMIERE_TIMEBASE)


@dataclass(frozen=True)
class TimelapseSchema:

    def __call__(self, output_path: Path, settings: TimelapseSettings) -> Path:
        timeline_sounds = settings.timeline_sound_paths

        n_frames = settings.sources.frames_count
        first_frame = settings.sources.first_frame.name

        fps_ticks = int(PREMIERE_TIMEBASE / settings.fps)
        frames_dur = n_frames * fps_ticks

        # The cover, if there is one, is shown as one extra frame before the
        # sequence proper, so it adds one frame's worth of length.
        n_seq_frames = n_frames
        if settings.cover:
            n_seq_frames += 1
        seq_dur = n_seq_frames * fps_ticks

        xml = Xml.from_prproj(_TEMPLATE_PATH)

        self._substitute_paths(xml, settings, first_frame)
        self._substitute_ticks(xml, fps_ticks, frames_dur, seq_dur)
        self._clear_audio_caches(xml)

        if not settings.sounds:
            self._remove_sound(xml)
        else:
            first_sound_name = settings.sounds[0].name

            if first_sound_name != _TMPL_SOUND_NAME:
                xml.xml = xml.xml.replace(f"./sound/{_TMPL_SOUND_NAME}", f"./sound/{first_sound_name}")
                xml.xml = xml.xml.replace(_TMPL_SOUND_NAME, first_sound_name)

            if Path(first_sound_name).suffix.lower() in _AUDIO_ONLY_EXTS:
                self._adapt_sound_to_audio_only(xml, first_sound_name)

            if len(settings.sounds) > 1:
                self._add_extra_sounds(xml, settings.sounds, bool(timeline_sounds))

            keep_on_timeline = {sound.name for sound in timeline_sounds}
            self._remove_sounds_from_timeline(xml, keep_on_timeline)

            if timeline_sounds:
                self._layout_sounds_in_timeline(xml, timeline_sounds)

        if not settings.cover:
            self._remove_cover(xml, fps_ticks, frames_dur, seq_dur)

        xml.remove_dangling_refs()
        xml.to_prproj(output_path)

        return output_path

    @staticmethod
    def _substitute_paths(xml: Xml, settings: TimelapseSettings, first_frame: str) -> None:
        # Premiere uses relative paths (./frames/, ./sound/) to locate media,
        # so we only need to swap the per-filename placeholders and the project name.
        xml.xml = xml.xml.replace(f"./frames/{_TMPL_FIRST_FRAME}", f"./frames/{first_frame}")
        xml.xml = xml.xml.replace(_TMPL_FIRST_FRAME, first_frame)
        xml.xml = xml.xml.replace(_TMPL_PHOTOSET, settings.name)

    @staticmethod
    def _substitute_ticks(xml: Xml, fps_ticks: int, frames_dur: int, seq_dur: int) -> None:
        # Frame rate: how long one frame lasts.
        for tag in ("OveriddenFrameRate", "FrameRate"):
            xml.xml = xml.xml.replace(f"<{tag}>{_TMPL_FPS_TICKS}</{tag}>", f"<{tag}>{fps_ticks}</{tag}>")

        xml.xml = xml.xml.replace(f"<End>{_TMPL_FPS_TICKS}</End>", f"<End>{fps_ticks}</End>")          # where the cover frame ends
        xml.xml = xml.xml.replace(f"<Start>{_TMPL_FPS_TICKS}</Start>", f"<Start>{fps_ticks}</Start>")  # where the frames clip starts
        xml.xml = xml.xml.replace(f"<End>{_TMPL_SEQ_DUR}</End>", f"<End>{seq_dur}</End>")              # where the frames clip ends (after the cover)

        for tag in ("OriginalDuration", "OutPoint", "MZ.WorkOutPoint"):
            xml.xml = xml.xml.replace(f"<{tag}>{_TMPL_FRAMES_DUR}</{tag}>", f"<{tag}>{frames_dur}</{tag}>")

    @staticmethod
    def _clear_audio_caches(xml: Xml) -> None:
        # The template remembers where it cached the waveform/peaks for its own
        # sound, on the machine it was made on. Blank those paths so Premiere
        # rebuilds the cache for our sound instead of trusting stale files.
        xml.xml = re.sub(r'<ConformedAudioPath>[^<]+</ConformedAudioPath>', '<ConformedAudioPath></ConformedAudioPath>', xml.xml)
        xml.xml = re.sub(r'<PeakFilePath>[^<]+</PeakFilePath>', '<PeakFilePath></PeakFilePath>', xml.xml)

    @staticmethod
    def _adapt_sound_to_audio_only(xml: Xml, sound_name: str) -> None:
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
        blocks = xml.toplevel_blocks()

        # The sound's Media chunk is where the video-stream pointer lives.
        sound_media = next(
            (b for b in blocks if sound_name in b.text and b.tag == "Media"),
            None,
        )
        if sound_media is None:
            return
        video_stream_ref = re.search(r'<VideoStream ObjectRef="(\d+)"/>', sound_media.text)
        if video_stream_ref is None:
            return  # no video part — already an audio-only sound, nothing to do
        video_stream_id = video_stream_ref.group(1)

        # Remove the video-stream pointer from the Media chunk.
        media_without_video = sound_media.text.replace(f'\t\t<VideoStream ObjectRef="{video_stream_id}"/>\n', '')
        xml.xml = xml.xml[:sound_media.start] + media_without_video + xml.xml[sound_media.end:]
        blocks = xml.toplevel_blocks()

        # The MasterClip lists its clips: slot 0 is the VideoClip, slot 1 the AudioClip.
        master_clip = next(
            (b for b in blocks if sound_name in b.text and b.tag == "MasterClip"),
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
        xml.remove_blocks_by_positions(to_delete)

        # Fix up the MasterClip's clip list: drop the VideoClip entry (slot 0)
        # and move the AudioClip from slot 1 to slot 0.
        if video_clip_id and master_clip:
            blocks = xml.toplevel_blocks()
            master_clip = next(
                (b for b in blocks if sound_name in b.text and b.tag == "MasterClip"),
                None,
            )
            if master_clip:
                clips_list = master_clip.text
                clips_list = clips_list.replace(f'\t\t<Clip Index="0" ObjectRef="{video_clip_id}"/>\n', '')
                clips_list = re.sub(r'<Clip Index="1" ObjectRef=', '<Clip Index="0" ObjectRef=', clips_list, count=1)
                xml.xml = xml.xml[:master_clip.start] + clips_list + xml.xml[master_clip.end:]

    @staticmethod
    def _remove_sound(xml: Xml) -> None:
        """Remove the template's sound completely (this timelapse has none)."""
        sound_blocks = [b for b in xml.toplevel_blocks() if _TMPL_SOUND_NAME in b.text]
        xml.remove_blocks_by_positions([(b.start, b.end) for b in sound_blocks])

    # В чем прикол именно экстра саундс? Почему нельзя сделать... То есть есть какой-то первый саунд и к нему добавляются остальные, а почему нельзя просто взять и добавить все вместе? Типа убираем исходный и добавляем новые туда же.
    @staticmethod
    def _add_extra_sounds(xml: Xml, sounds: list[Path], timeline: bool = False) -> None:
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
        blocks = xml.toplevel_blocks()
        first_name = sounds[0].name

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

        max_id = max(int(i) for i in re.findall(r'ObjectID="(\d+)"', xml.xml))
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

        xml.xml = xml.xml[:insert_pos] + cloned_blocks + xml.xml[insert_pos:]

        # Add the copies to the project's clip list, right after the original, so
        # they actually show up in the project panel.
        if first_panel_item_uid and new_panel_item_uids:
            original_item = re.search(rf'<Item Index="(\d+)" ObjectURef="{re.escape(first_panel_item_uid)}"', xml.xml)
            if original_item:
                base_index = int(original_item.group(1))
                added_items = "".join(
                    f'\n\t\t\t\t<Item Index="{base_index + offset}" ObjectURef="{uid}"/>'
                    for offset, uid in enumerate(new_panel_item_uids, start=1)
                )
                xml.xml = xml.xml.replace(
                    f'<Item Index="{base_index}" ObjectURef="{first_panel_item_uid}"/>',
                    f'<Item Index="{base_index}" ObjectURef="{first_panel_item_uid}"/>{added_items}',
                )

        if timeline and new_track_item_ids and first_track_item_id:
            TimelapseSchema._append_track_items(xml, first_track_item_id, new_track_item_ids)

    @staticmethod
    def _layout_sounds_in_timeline(xml: Xml, sounds: list[Path]) -> None:
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
            blocks = xml.toplevel_blocks()
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
            xml.xml = xml.xml[:track_item.start] + positioned + xml.xml[track_item.end:]

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
                        (b for b in xml.toplevel_blocks()
                         if b.tag == "AudioClip" and f'ObjectID="{audio_clip_ref.group(1)}"' in b.text[:120]),
                        None,
                    )
                    if audio_clip:
                        xml.xml = xml.xml[:audio_clip.start] + trimmed + xml.xml[audio_clip.end:]

            placed_ids.add(track_item_id)
            cursor = end

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
    def _remove_sounds_from_timeline(xml: Xml, keep_names: set[str] = frozenset()) -> None:
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
        blocks = xml.toplevel_blocks()
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
            return

        keep_entry = [i for i, b in enumerate(blocks) if b.tag == "ClipProjectItem"] + kept
        keep_closure = set(_collect_sound_closure(blocks, keep_entry))
        dropped_closure = set(_collect_sound_closure(blocks, dropped))
        to_remove = (dropped_closure - keep_closure) | set(dropped)

        dropped_ids = [re.search(r'ObjectID="(\d+)"', blocks[i].text[:120]).group(1) for i in dropped]
        xml.remove_blocks_by_positions([(blocks[i].start, blocks[i].end) for i in to_remove])
        for track_item_id in dropped_ids:
            xml.xml = re.sub(rf'[^\S\n]*<TrackItem Index="\d+" ObjectRef="{track_item_id}"/>\n', '', xml.xml)

    @staticmethod
    def _append_track_items(xml: Xml, anchor_id: str, track_item_ids: list[str]) -> None:
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

        xml.xml = re.sub(
            rf'<TrackItems Version="\d+">(?:(?!</TrackItems>).)*?'
            rf'<TrackItem Index="\d+" ObjectRef="{anchor_id}"/>.*?</TrackItems>',
            append_after_last, xml.xml, count=1, flags=re.DOTALL,
        )

    # Здесь нужно еще обработать кейс, когда кавер на таймлайне, но мы его удаляем и соответственно надо весь таймлайн сдвинуть влево.
    # Или это здесь уже обрабатывается что ли?
    @staticmethod
    def _remove_cover(xml: Xml, fps_ticks: int, frames_dur: int, seq_dur: int) -> None:
        """Remove the cover frame and slide the image sequence back to the start."""
        # Cut the cover's own media chunks (the ones that name cover.jpg). The
        # rest of the cover's cluster (its VideoClip, its timeline slot, its slot
        # list entry) then has nothing pointing to it, so remove_dangling_refs
        # sweeps it away for us.
        cover_blocks = [b for b in xml.toplevel_blocks() if "cover.jpg" in b.text]
        xml.remove_blocks_by_positions([(b.start, b.end) for b in cover_blocks])
        xml.remove_dangling_refs()

        # The frames clip used to sit one cover-frame in, from [fps_ticks → seq_dur].
        # With the cover gone it starts at the very beginning: [0 → frames_dur].
        xml.xml = xml.xml.replace(f"<Start>{fps_ticks}</Start>", "<Start>0</Start>")
        xml.xml = xml.xml.replace(f"<End>{seq_dur}</End>", f"<End>{frames_dur}</End>")


def generate_prproj(settings: TimelapseSettings) -> Path:
    output_path = settings.timelapse_dir / f"{settings.name}.prproj"

    # Don't clobber an existing project (it may have been edited by hand) — pick
    # the next free numbered name instead.
    if output_path.exists():
        i = 1
        while (candidate := settings.timelapse_dir / f"{settings.name}_{i}.prproj").exists():
            i += 1
        output_path = candidate

    frames_line = str(settings.sources.frames_count)
    if settings.cover:
        frames_line += " + cover"
    timeline_line = [s.name for s in settings.timeline_sound_paths] or "panel only"

    print(f"Photoset:  {settings.name}")
    print(f"Frames:    {frames_line}")
    print(f"Sounds:    {[s.name for s in settings.sounds]}")
    print(f"FPS:       {settings.fps}")
    print(f"Timeline:  {timeline_line}")

    return TimelapseSchema()(output_path, settings)
