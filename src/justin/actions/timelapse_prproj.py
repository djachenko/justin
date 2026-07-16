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
  * replace the template's placeholder sound with the real sounds — cloning its
    block cluster once per sound, and stripping the video part for audio-only
    files like mp3 (``_place_sounds`` / ``Sound.adapt``);
  * keep chosen sounds on the timeline (a panel-only sound has its slot stripped
    from the clone), then line the timeline sounds up back-to-back
    (``_lay_out_timeline``);
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

import subprocess
from dataclasses import dataclass
from importlib.resources import files as _resource_files
from pathlib import Path

from justin.actions.timelapse_block import Block, Blocks
from justin.actions.timelapse_settings import TimelapseSettings
from justin.actions.timelapse_sound import Sound
from justin.actions.timelapse_sources import TimelapseSources
from justin.actions.timelapse_tags import Tag
from justin.actions.timelapse_xml import Xml, _CLIP_MEDIA_TYPES
from justin.actions.timelapse_xml_ops import TimelapseXmlOps

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

_FPS_TICKS_TAGS = (
    "OveriddenFrameRate",  # VideoStream: interpreted fps of the image sequence, ticks per frame
    "FrameRate",           # TrackGroup: sequence (timeline) fps, ticks per frame
    "End",                 # where the cover frame ends, ticks
    "Start",               # where the frames clip starts, ticks
)

_FRAMES_DUR_TAGS = (
    "OriginalDuration",    # native clip length, ticks
    "OutPoint",            # where the clip ends in the viewer, ticks
    "MZ.WorkOutPoint",     # work area end (render range), ticks
)



def _resolve_timeline_sounds(sounds: list[Sound], timeline_sounds: list[str]) -> list[Sound]:
    return [sound for sound in sounds if sound.name in timeline_sounds or sound.stem in timeline_sounds]



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

    def __call__(
        self,
        output_path: Path,
        sources: TimelapseSources,
        settings: TimelapseSettings = TimelapseSettings(),
    ) -> Path:
        sounds = sources.sounds or []
        timeline_sounds = _resolve_timeline_sounds(sounds, settings.timeline_sounds)

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
            self._place_sounds(xml, sounds, {sound.name for sound in timeline_sounds})

            if timeline_sounds:
                self._lay_out_timeline(xml, timeline_sounds)

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
        for tag in _FPS_TICKS_TAGS:
            xml.replace(f"<{tag}>{_TMPL_FPS_TICKS}</{tag}>", f"<{tag}>{ticks_per_frame}</{tag}>")

        # End of the frames clip on the timeline: it sits right after the cover
        # frame, so in the template this is the whole sequence (cover + all frames).
        # With no cover, _remove_cover pulls it back to image_sequence_duration.
        xml.replace(f"<End>{_TMPL_SEQ_DUR}</End>", f"<End>{sequence_duration}</End>")

        for tag in _FRAMES_DUR_TAGS:
            xml.replace(f"<{tag}>{_TMPL_FRAMES_DUR}</{tag}>", f"<{tag}>{image_sequence_duration}</{tag}>")

    @staticmethod
    def _clear_audio_caches(xml: Xml) -> None:
        TimelapseXmlOps.clear_audio_cache_paths(xml)

    @staticmethod
    def _remove_sound(xml: Xml) -> None:
        """Remove the template's sound completely (this timelapse has none)."""
        sound_blocks = xml.toplevel_blocks().containing(_SOUND_NAME_MARKER)

        xml.remove_blocks_by_positions([b.span for b in sound_blocks])

    @staticmethod
    def _place_sounds(xml: Xml, sounds: list[Sound], timeline_names: set[str]) -> None:
        """
        Replace the template's placeholder sound with the real sounds.

        The template carries one sound as a full cluster: a project-panel clip
        plus a timeline slot. We clone that cluster once per real sound (fresh
        ids, the real filename); a sound not wanted on the timeline has its slot
        stripped from the clone first, so it stays panel-only. Clones go in before
        the template comes out — the template's positions stay valid while we
        splice in after them — and the template's own slot leaves with it.
        Audio-only sounds (mp3, wav, …) then get their video part stripped; stale
        panel/track list entries are swept later by remove_dangling_refs.
        """
        blocks = xml.toplevel_blocks()
        seeds = blocks.containing(_SOUND_NAME_MARKER) + blocks.by_tag(Tag.AudioClipTrackItem)
        template = blocks.reachable_cluster(seeds, _CLIP_MEDIA_TYPES)

        # Anchors in the template's panel/track lists, read before it disappears.
        template_panel = template.by_tag(Tag.ClipProjectItem).first()
        template_panel_uid = TimelapseXmlOps.block_uid(template_panel.text) if template_panel else None
        template_slot = template.by_tag(Tag.AudioClipTrackItem).first()
        template_slot_id = template_slot.id if template_slot else None

        insert_at = max(block.end for block in template)
        max_id = xml.max_object_id()

        clones = ""
        panel_uids: list[str] = []
        slot_ids: list[str] = []

        for n, sound in enumerate(sounds, start=1):
            clone = TimelapseXmlOps.clone_sound_blocks(template, _SOUND_NAME_MARKER, sound.name, (max_id + 1) * n)
            on_timeline = sound.name in timeline_names

            if not on_timeline:
                clone = TimelapseSchema._strip_timeline_slot(clone)

            clones += clone

            if uid := TimelapseXmlOps.clip_project_item_uid(clone):
                panel_uids.append(uid)

            if on_timeline and (slot_id := TimelapseXmlOps.audio_clip_track_item_id(clone)):
                slot_ids.append(slot_id)

        xml.insert(insert_at, clones)
        xml.remove_blocks_by_positions([block.span for block in template])

        for sound in sounds:
            sound.adapt(xml)

        TimelapseSchema._register_in_panel(xml, template_panel_uid, panel_uids)

        if template_slot_id and slot_ids:
            TimelapseXmlOps.append_track_items_after(xml, template_slot_id, slot_ids)

    @staticmethod
    def _strip_timeline_slot(clone: str) -> str:
        """Cut a clone's timeline slot so its sound stays panel-only.

        Removes the slot and the blocks only it uses — its own SubClip, AudioClip
        and component chain — worked out as everything reachable from the slot
        minus everything the panel clip (its ClipProjectItem) still needs, so the
        shared panel blocks stay put.
        """
        fragment = Xml(clone)
        blocks = fragment.toplevel_blocks()
        slots = blocks.by_tag(Tag.AudioClipTrackItem)

        if not slots:
            return clone

        panel_cluster = blocks.reachable_cluster(blocks.by_tag(Tag.ClipProjectItem), _CLIP_MEDIA_TYPES)
        panel_starts = {block.start for block in panel_cluster}
        slot_only = [block for block in blocks.reachable_cluster(slots, _CLIP_MEDIA_TYPES)
                     if block.start not in panel_starts]

        fragment.remove_blocks_by_positions([block.span for block in slot_only])

        return fragment.text

    @staticmethod
    def _register_in_panel(xml: Xml, template_uid: str | None, clone_uids: list[str]) -> None:
        """List the cloned clips in the project panel, right after the template's entry."""
        if not (template_uid and clone_uids):
            return

        anchor_index = xml.find_panel_item_index(template_uid)

        if anchor_index is None:
            return

        added = "".join(
            f'\n\t\t\t\t<Item Index="{anchor_index + offset}" ObjectURef="{uid}"/>'
            for offset, uid in enumerate(clone_uids, start=1)
        )

        xml.replace(
            f'<Item Index="{anchor_index}" ObjectURef="{template_uid}"/>',
            f'<Item Index="{anchor_index}" ObjectURef="{template_uid}"/>{added}',
        )

    @staticmethod
    def _lay_out_timeline(xml: Xml, sounds: list[Sound]) -> None:
        """
        Line the timeline sounds up back-to-back at their real lengths.

        Each sound's real length comes from ffprobe. The first sound starts at 0,
        the next starts where it ended, and so on. For each slot we set two things:
        where it sits on the track (its Start/End) and how much of the clip plays
        (the AudioClip's OutPoint, reached through the slot's SubClip). Every edit
        is worked out up front, then applied from the end of the document backwards
        so the byte offsets stay valid.
        """
        durations = {sound.name: _probe_duration_ticks(sound.path) for sound in sounds}
        blocks = xml.toplevel_blocks()

        slots = [
            slot for slot in blocks.by_tag(Tag.AudioClipTrackItem)
            if TimelapseSchema._track_item_sound_name(slot, blocks) in durations
        ]

        edits: list[tuple[int, int, str]] = []
        cursor = 0

        for slot in slots:
            duration = durations[TimelapseSchema._track_item_sound_name(slot, blocks)]
            end = cursor + duration

            # Where the clip sits on the track. It always has an end; it gets a
            # start only once we're past 0 (the first clip has none, matching how
            # the template stores it).
            edits.append((*slot.span, TimelapseXmlOps.set_slot_position(slot.text, cursor or None, end)))

            # How much of the clip plays — the AudioClip reached through the slot's SubClip.
            subclip = blocks.by_id(Tag.SubClip, TimelapseXmlOps.subclip_ref(slot.text))
            audio_clip = blocks.by_id(Tag.AudioClip, TimelapseXmlOps.clip_ref(subclip.text)) if subclip else None

            if audio_clip and "<OutPoint>" in audio_clip.text:
                edits.append((*audio_clip.span, TimelapseXmlOps.set_out_point(audio_clip.text, duration)))

            cursor = end

        xml.replace_ranges(edits)

    @staticmethod
    def _track_item_sound_name(track_item: Block, blocks: Blocks) -> str | None:
        """Which sound file a timeline slot plays (read off its SubClip's Name)."""
        subclip = blocks.by_id(Tag.SubClip, TimelapseXmlOps.subclip_ref(track_item.text))

        return TimelapseXmlOps.block_name(subclip.text) if subclip else None

    @staticmethod
    def _remove_cover(xml: Xml, ticks_per_frame: int, image_sequence_duration: int, sequence_duration: int) -> None:
        """Remove the cover frame and slide the image sequence back to the start."""
        # Cut the cover's own media chunks (the ones that name cover.jpg). The
        # rest of the cover's cluster (its VideoClip, its timeline slot, its slot
        # list entry) then has nothing pointing to it, so remove_dangling_refs
        # sweeps it away for us.
        cover_blocks = xml.toplevel_blocks().containing("cover.jpg")

        xml.remove_blocks_by_positions([b.span for b in cover_blocks])
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
        suffix = 1
        while (candidate := sources.folder / f"{sources.name}_{suffix}.prproj").exists():
            suffix += 1
        output_path = candidate

    sounds = sources.sounds or []
    timeline_sounds = _resolve_timeline_sounds(sounds, settings.timeline_sounds)

    frames_line = str(sources.frames_count)
    if sources.cover:
        frames_line += " + cover"
    timeline_line = [s.name for s in timeline_sounds] or "panel only"

    print(f"Photoset:  {sources.name}")
    print(f"Frames:    {frames_line}")
    print(f"Sounds:    {[s.name for s in sounds]}")
    print(f"FPS:       {settings.fps}")
    print(f"Timeline:  {timeline_line}")

    return TimelapseSchema()(output_path, sources, settings)
