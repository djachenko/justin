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
``template.prproj`` — an image sequence + a cover frame + one sound on the
timeline, 10 fps, with abstract placeholder strings). We open that file's text
and carefully edit it to describe the timelapse we actually want:

  * swap in the right folder paths, frame count, and durations (``_substitute_*``);
  * replace the template's placeholder sound with the real sounds — including
    stripping the video part for audio-only files like mp3 (``Sound.adapt``);
  * copy the sound's block cluster once per real sound (``_apply_sounds``);
  * put chosen sounds on the timeline, or leave them only in the project's clip
    list (``_layout_sounds_in_timeline`` / ``_remove_sounds_from_timeline``);
  * throw away the cover frame or the sound entirely if the timelapse has none.

Every block carries ids so other blocks can refer to it. There are two flavors
of id, and the difference bites you if you ignore it:

  * ``ObjectID`` / ``ObjectRef`` — plain small numbers. A number is unique only
    among blocks of the *same kind*, so number 56 can name several different
    blocks of different kinds. Don't assume a number is globally unique.
  * ``ObjectUID`` / ``ObjectURef`` — long random codes (uuids), unique everywhere.

We do almost all the editing one block at a time: ``toplevel_blocks``
finds where each block starts and ends in the raw text, and we cut blocks out or
splice them back in with ordinary string slicing.
"""

import re
import subprocess
from dataclasses import dataclass
from importlib.resources import files as _resource_files
from pathlib import Path
from typing import TypeVar, Iterable, Callable

from justin.actions.timelapse_settings import TimelapseSettings
from justin.actions.timelapse_sources import TimelapseSources
from justin.actions.timelapse_sound import Sound
from justin.actions.timelapse_xml import (
    Xml,
    block_id,
    collect_sound_closure as _collect_sound_closure,
    clone_sound_blocks as _clone_sound_blocks,
    _OBJECT_ID_RE,
    _OBJECT_UID_RE,
)

# Premiere measures time in "ticks". This many ticks make one second.
PREMIERE_TIMEBASE = 254_016_000_000

_TEMPLATE_DATA: bytes = (
    _resource_files("justin.resources.timelapse_templates")
    .joinpath("template.prproj")
    .read_bytes()
)

# Placeholder strings baked into the template. Each substitute_* method swaps
# these out for the real values of the target timelapse.
_FIRST_FRAME_MARKER   = "TMPL_FIRST_FRAME.jpg"
_PHOTOSET_NAME_MARKER      = "TMPL_PHOTOSET"
_SOUND_NAME_MARKER    = "TMPL_SOUND.mp4"

# Numeric values baked into the template (106 frames at 10 fps + 1 cover frame).
_TMPL_FPS_TICKS  = int(PREMIERE_TIMEBASE / 10)
_TMPL_N_FRAMES   = 106
_TMPL_FRAMES_DUR = _TMPL_N_FRAMES * _TMPL_FPS_TICKS
_TMPL_SEQ_DUR    = (_TMPL_N_FRAMES + 1) * _TMPL_FPS_TICKS

# Formats that carry sound only, no picture. The template's sound is an mp4
# (which has a video part), so for these we have to remove that video part —
# see _adapt_sound_to_audio_only.



def _resolve_timeline_sounds(sounds: list[Sound], timeline_sounds: list[str]) -> list[Sound]:
    return [s for s in sounds if s.name in timeline_sounds or s.stem in timeline_sounds]



def _probe_duration_ticks(path: Path) -> int:
    """Ask ffprobe how long a media file is, and give it back in Premiere ticks."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )

    return int(float(probe.stdout.strip()) * PREMIERE_TIMEBASE)

T = TypeVar("T")

def indices_of_matching(items: Iterable[T], predicate: Callable[[T], bool]) -> list[int]:
    return [index for index, item in enumerate(items) if predicate(item)]


@dataclass(frozen=True)
class TimelapseSchema:

    def __call__(
        self,
        output_path: Path,
        sources: TimelapseSources,
        settings: TimelapseSettings = TimelapseSettings(),
    ) -> Path:
        sounds = sources.sounds or []
        timeline_sound_paths = _resolve_timeline_sounds(sounds, settings.timeline_sounds)

        frame_count = sources.frames_count
        first_frame = sources.first_frame.name

        ticks_per_frame = int(PREMIERE_TIMEBASE / settings.fps)
        image_sequence_duration = frame_count * ticks_per_frame
        # The cover occupies one extra frame at the start of the sequence.
        sequence_duration = (frame_count + (1 if sources.cover else 0)) * ticks_per_frame

        xml = Xml.from_gzip_bytes(_TEMPLATE_DATA)

        self._substitute_paths(xml, sources.name, first_frame)
        self._substitute_ticks(xml, ticks_per_frame, image_sequence_duration, sequence_duration)
        self._clear_audio_caches(xml)

        if not sounds:
            self._remove_sound(xml)
        else:
            self._apply_sounds(xml, sounds, bool(timeline_sound_paths))

            keep_on_timeline = {sound.name for sound in timeline_sound_paths}
            self._remove_sounds_from_timeline(xml, keep_on_timeline)

            if timeline_sound_paths:
                self._layout_sounds_in_timeline(xml, timeline_sound_paths)

        if not sources.cover:
            self._remove_cover(xml, ticks_per_frame, image_sequence_duration, sequence_duration)

        xml.remove_dangling_refs()
        xml.to_prproj(output_path)

        return output_path

    @staticmethod
    def _substitute_paths(xml: Xml, name: str, first_frame: str) -> None:
        # Premiere uses relative paths (./frames/, ./sound/) to locate media,
        # so we only need to swap the per-filename placeholders and the project name.
        xml.replace(f"./frames/{_FIRST_FRAME_MARKER}", f"./frames/{first_frame}")
        xml.replace(_FIRST_FRAME_MARKER, first_frame)
        xml.replace(_PHOTOSET_NAME_MARKER, name)

    @staticmethod
    def _substitute_ticks(xml: Xml, ticks_per_frame: int, image_sequence_duration: int, sequence_duration: int) -> None:
        # Frame rate: how long one frame lasts.
        for tag in ("OveriddenFrameRate", "FrameRate"):
            xml.replace(f"<{tag}>{_TMPL_FPS_TICKS}</{tag}>", f"<{tag}>{ticks_per_frame}</{tag}>")

        xml.replace(f"<End>{_TMPL_FPS_TICKS}</End>", f"<End>{ticks_per_frame}</End>")          # where the cover frame ends
        xml.replace(f"<Start>{_TMPL_FPS_TICKS}</Start>", f"<Start>{ticks_per_frame}</Start>")  # where the frames clip starts
        xml.replace(f"<End>{_TMPL_SEQ_DUR}</End>", f"<End>{sequence_duration}</End>")          # where the frames clip ends (after the cover)

        for tag in ("OriginalDuration", "OutPoint", "MZ.WorkOutPoint"):
            xml.replace(f"<{tag}>{_TMPL_FRAMES_DUR}</{tag}>", f"<{tag}>{image_sequence_duration}</{tag}>")

    @staticmethod
    def _clear_audio_caches(xml: Xml) -> None:
        # The template remembers where it cached the waveform/peaks for its own
        # sound, on the machine it was made on. Blank those paths so Premiere
        # rebuilds the cache for our sound instead of trusting stale files.
        xml.sub(r'<ConformedAudioPath>[^<]+</ConformedAudioPath>', '<ConformedAudioPath></ConformedAudioPath>')
        xml.sub(r'<PeakFilePath>[^<]+</PeakFilePath>', '<PeakFilePath></PeakFilePath>')

    @staticmethod
    def _remove_sound(xml: Xml) -> None:
        """Remove the template's sound completely (this timelapse has none)."""
        sound_blocks = [b for b in xml.toplevel_blocks() if _SOUND_NAME_MARKER in b.text]

        xml.remove_blocks_by_positions([(b.start, b.end) for b in sound_blocks])

    @staticmethod
    def _apply_sounds(xml: Xml, sounds: list[Sound], timeline: bool = False) -> None:
        """
        Replace the template's placeholder sound with all the real sounds.

        The template carries one sound (TMPL_SOUND.mp4). We extract its block cluster
        as a cloning source, produce one clone per real sound — each with fresh ids and
        the real filename — then remove the template. Inserting the clones before the
        removal keeps the template's block positions valid.

        If ``timeline`` is True each clone also carries a timeline slot; those are
        registered on the audio track. Audio-only sounds (mp3, wav, …) get their video
        part stripped after insertion.
        """
        blocks = xml.toplevel_blocks()

        # Seed the closure with blocks that name the template sound. Include the
        # timeline slot only when clones should carry one too.
        seed = indices_of_matching(blocks, lambda block: _SOUND_NAME_MARKER in block.text)

        if timeline:
            seed += indices_of_matching(blocks, lambda block: block.tag == "AudioClipTrackItem")

        tmpl_blocks = [blocks[i] for i in _collect_sound_closure(blocks, seed)]

        # Grab registration anchors before the template disappears.
        tmpl_panel = next((b for b in tmpl_blocks if b.tag == "ClipProjectItem"), None)
        tmpl_panel_uid = re.search(_OBJECT_UID_RE, tmpl_panel.text).group(1) if tmpl_panel else None

        tmpl_track = next((b for b in tmpl_blocks if b.tag == "AudioClipTrackItem"), None)
        tmpl_track_id = block_id(tmpl_track) if tmpl_track else None

        insert_pos = max(b.end for b in tmpl_blocks)
        max_id = max(int(i) for i in re.findall(_OBJECT_ID_RE, xml._xml))

        all_clones = ""
        new_panel_uids: list[str] = []
        new_track_ids: list[str] = []

        for i, sound in enumerate(sounds, start=1):
            clone = _clone_sound_blocks(tmpl_blocks, _SOUND_NAME_MARKER, sound.name, (max_id + 1) * i)
            all_clones += clone

            if match := re.search(r'<ClipProjectItem ' + _OBJECT_UID_RE, clone):
                new_panel_uids.append(match.group(1))

            if match := re.search(r'<AudioClipTrackItem ' + _OBJECT_ID_RE, clone):
                new_track_ids.append(match.group(1))

        # Insert clones first (template positions still valid), then remove the template.
        # The stale panel/timeline entries are swept by remove_dangling_refs at the end.
        xml.insert(insert_pos, all_clones)
        xml.remove_blocks_by_positions([(b.start, b.end) for b in tmpl_blocks])

        for sound in sounds:
            sound.adapt(xml)

        # Register new clips in the project panel, anchored after the stale template entry.
        if tmpl_panel_uid and new_panel_uids:
            anchor = re.search(rf'<Item Index="(\d+)" ObjectURef="{re.escape(tmpl_panel_uid)}"', xml._xml)

            if anchor:
                base = int(anchor.group(1))

                added = "".join(
                    f'\n\t\t\t\t<Item Index="{base + j}" ObjectURef="{uid}"/>'
                    for j, uid in enumerate(new_panel_uids, start=1)
                )

                xml.replace(
                    f'<Item Index="{base}" ObjectURef="{tmpl_panel_uid}"/>',
                    f'<Item Index="{base}" ObjectURef="{tmpl_panel_uid}"/>{added}',
                )

        # Register clone timeline slots on the audio track.
        if timeline and new_track_ids and tmpl_track_id:
            TimelapseSchema._append_track_items(xml, tmpl_track_id, new_track_ids)

    @staticmethod
    def _layout_sounds_in_timeline(xml: Xml, sounds: list[Sound]) -> None:
        """
        Line the timeline sounds up back-to-back at their real lengths.

        Each sound's real length comes from ffprobe. The first sound starts at 0,
        the next starts where it ended, and so on. For each sound we set two
        things: the timeline slot's start/end (where the clip sits on the track)
        and the clip's own end point (how much of the clip plays). Slots are
        matched to sounds by filename and handled in the order they appear.
        """
        durations = {sound.name: _probe_duration_ticks(sound.path) for sound in sounds}
        cursor = 0
        placed_ids: set[str] = set()

        while True:
            blocks = xml.toplevel_blocks()

            block_text_by_id = {
                (b.tag, block_id(b)): b.text
                for b in blocks if block_id(b)
            }

            # Find the next timeline slot we haven't placed yet whose sound we know.
            track_item = next(
                (b for b in blocks
                 if b.tag == "AudioClipTrackItem"
                 and block_id(b) not in placed_ids
                 and TimelapseSchema._track_item_sound_name(b.text, block_text_by_id) in durations),
                None,
            )

            if track_item is None:
                break

            track_item_id = block_id(track_item)
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

            xml.replace_range(track_item.start, track_item.end, positioned)

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
                         if b.tag == "AudioClip" and block_id(b) == audio_clip_ref.group(1)),
                        None,
                    )
                    if audio_clip:
                        xml.replace_range(audio_clip.start, audio_clip.end, trimmed)

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
            (b.tag, block_id(b)): b.text
            for b in blocks if block_id(b)
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

        dropped_ids = [block_id(blocks[i]) for i in dropped]
        xml.remove_blocks_by_positions([(blocks[i].start, blocks[i].end) for i in to_remove])
        for track_item_id in dropped_ids:
            xml.sub(rf'[^\S\n]*<TrackItem Index="\d+" ObjectRef="{track_item_id}"/>\n', '')

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

        xml.sub(
            rf'<TrackItems Version="\d+">(?:(?!</TrackItems>).)*?'
            rf'<TrackItem Index="\d+" ObjectRef="{anchor_id}"/>.*?</TrackItems>',
            append_after_last, count=1, flags=re.DOTALL,
        )

    @staticmethod
    def _remove_cover(xml: Xml, ticks_per_frame: int, image_sequence_duration: int, sequence_duration: int) -> None:
        """Remove the cover frame and slide the image sequence back to the start."""
        # Cut the cover's own media chunks (the ones that name cover.jpg). The
        # rest of the cover's cluster (its VideoClip, its timeline slot, its slot
        # list entry) then has nothing pointing to it, so remove_dangling_refs
        # sweeps it away for us.
        cover_blocks = [b for b in xml.toplevel_blocks() if "cover.jpg" in b.text]

        xml.remove_blocks_by_positions([(b.start, b.end) for b in cover_blocks])
        xml.remove_dangling_refs()

        # The frames clip used to sit one cover-frame in, from [ticks_per_frame → sequence_duration].
        # With the cover gone it starts at the very beginning: [0 → image_sequence_duration].
        xml.replace(f"<Start>{ticks_per_frame}</Start>", "<Start>0</Start>")
        xml.replace(f"<End>{sequence_duration}</End>", f"<End>{image_sequence_duration}</End>")


def generate_prproj(sources: TimelapseSources, settings: TimelapseSettings = TimelapseSettings()) -> Path:
    output_path = sources.folder / f"{sources.name}.prproj"

    # Don't clobber an existing project (it may have been edited by hand) — pick
    # the next free numbered name instead.
    if output_path.exists():
        i = 1
        while (candidate := sources.folder / f"{sources.name}_{i}.prproj").exists():
            i += 1
        output_path = candidate

    sounds = sources.sounds or []
    timeline_sound_paths = _resolve_timeline_sounds(sounds, settings.timeline_sounds)

    frames_line = str(sources.frames_count)
    if sources.cover:
        frames_line += " + cover"
    timeline_line = [s.name for s in timeline_sound_paths] or "panel only"

    print(f"Photoset:  {sources.name}")
    print(f"Frames:    {frames_line}")
    print(f"Sounds:    {[s.name for s in sounds]}")
    print(f"FPS:       {settings.fps}")
    print(f"Timeline:  {timeline_line}")

    return TimelapseSchema()(output_path, sources, settings)
