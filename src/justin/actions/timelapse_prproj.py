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
``timelapse_template.prproj`` — an image sequence + a cover frame + one sound on the
timeline, 10 fps, with abstract placeholder strings). We open that file's text
and carefully edit it to describe the timelapse we actually want:

  * swap in the right folder paths, frame count, and durations (``_actualize_*``);
  * realize the template's sound as each real sound (rename + strip the video part
    for audio-only files like mp3, ``Sound.adapt``), give each a fresh id-space and
    put it in the project panel (``_place_in_panel``);
  * put the chosen sounds on the timeline and lay them out (``_place_on_timeline``);
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

from dataclasses import dataclass
from importlib.resources import files as _resource_files
from pathlib import Path

from justin.actions.timelapse_model import AudioClipTrackItem, Document
from justin.actions.timelapse_settings import TimelapseSettings
from justin.actions.timelapse_sound import Sound
from justin.actions.timelapse_sources import TimelapseSources
from justin.actions.timelapse_tags import Tag
from justin.actions.timelapse_template import TimelapseTemplate
from justin.actions import timelapse_ticks
from justin.actions.timelapse_xml import Xml, _CLIP_MEDIA_TYPES
from justin.actions.timelapse_xml_ops import TimelapseXmlOps

_TEMPLATE_DATA: bytes = (
    _resource_files("justin.resources.timelapse_templates")
    .joinpath("timelapse_template.prproj")
    .read_bytes()
)

# Placeholder strings baked into the template live in TimelapseTemplate; each
# _actualize_* method (and Sound.replace_name) swaps them for real values.

# Numeric values baked into the template (106 frames at 10 fps + 1 cover frame).
_TMPL_FPS_TICKS  = timelapse_ticks.ticks_per_frame(10)
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

        ticks_per_frame = timelapse_ticks.ticks_per_frame(settings.fps)
        image_sequence_duration = frame_count * ticks_per_frame

        # The cover occupies one extra frame at the start of the sequence.
        sequence_duration = frame_count * ticks_per_frame

        if sources.cover:
            sequence_duration += ticks_per_frame

        xml = Xml.from_gzip_bytes(_TEMPLATE_DATA)

        self._actualize_paths(xml, sources.name, first_frame) # paths to actual files
        self._actualize_ticks(xml, ticks_per_frame, image_sequence_duration, sequence_duration) # fps and durations
        self._clear_audio_caches(xml) # drop caches (they will be regenerated anyway)

        if not sounds:
            self._remove_sound(xml)
        else:
            template_slot_id, timeline_slots = self._place_in_panel(xml, sounds, {sound.name for sound in timeline_sounds})

            self._place_on_timeline(xml, template_slot_id, timeline_slots)

        if not sources.cover:
            self._remove_cover(xml, ticks_per_frame, image_sequence_duration, sequence_duration)

        xml.remove_dangling_refs()
        xml.to_prproj(output_path)

        return output_path

    @staticmethod
    def _actualize_paths(xml: Xml, name: str, first_frame: str) -> None:
        # Premiere uses relative paths (./frames/, ./sound/) to locate media,
        # so we only need to swap the per-filename placeholders and the project name.
        xml.replace(f"./frames/{TimelapseTemplate.FIRST_FRAME}", f"./frames/{first_frame}")
        xml.replace(TimelapseTemplate.FIRST_FRAME, first_frame)
        xml.replace(TimelapseTemplate.PHOTOSET, name)

    @staticmethod
    def _actualize_ticks(xml: Xml, ticks_per_frame: int, image_sequence_duration: int, sequence_duration: int) -> None:
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
        sound_blocks = xml.toplevel_blocks().containing(TimelapseTemplate.SOUND_NAME)

        xml.remove_blocks_by_positions([b.span for b in sound_blocks])

    @staticmethod
    def _place_in_panel(xml: Xml, sounds: list[Sound], timeline_names: set[str]) -> tuple[str | None, list[tuple[str, Sound]]]:
        """
        Realize every sound from the template and put it in the project panel.

        The template carries one sound as a full cluster: a project-panel clip plus a
        timeline slot fused to it (the slot shares the clip's audio media). We split it
        once — ``panel_template`` (the panel clip) and the full ``template`` (clip +
        slot). A sound wanted on the timeline is realized from the full template (its
        slot co-clones, so it stays wired to the clip for free); a panel-only sound
        from ``panel_template``.

        Two phases: **realize** — each Sound renames + adapts its own section, in the
        template's ids; **integrate** — assign each a fresh, non-clashing id-space,
        splice them in, register them in the panel. Returns the template slot id and
        the new slots as ``(slot id, sound)`` pairs, which is all the timeline needs.
        """
        blocks = xml.toplevel_blocks()
        panel_roots = blocks.containing(TimelapseTemplate.SOUND_NAME)
        timeline_roots = blocks.by_tag(Tag.AudioClipTrackItem)

        panel_template = blocks.reachable_cluster(panel_roots, _CLIP_MEDIA_TYPES)          # panel clip only
        timeline_template = blocks.reachable_cluster(panel_roots + timeline_roots, _CLIP_MEDIA_TYPES)        # + its timeline slot

        # Anchors: the template's own panel uid and slot id. Read them now, because
        # the template blocks are deleted at the end of this method. The <Item>/
        # <TrackItem> lines naming them sit outside the cluster and survive, so
        # afterwards we can still find them and splice the clones in right after.


        if template_panel := panel_template.by_tag(Tag.ClipProjectItem).first():
            template_panel_uid = TimelapseXmlOps.block_uid(template_panel.text)
        else:
            template_panel_uid = None

        if template_slot := timeline_template.by_tag(Tag.AudioClipTrackItem).first():
            template_slot_id = template_slot.id
        else:
            template_slot_id = None

        insert_at = max(block.end for block in timeline_template)
        max_id = xml.max_object_id()

        # realize: template → each sound's own section (renamed + adapted, template ids)
        new_sound_sections: list[str] = []

        for sound in sounds:
            if sound.name in timeline_names:
                source = timeline_template
            else:
                source = panel_template

            new_sound_sections.append(sound.adapt(str(source)))

        # integrate: fresh ids, splice in, collect what's registrable
        clones = ""
        panel_uids: list[str] = []
        timeline_slots: list[tuple[str, Sound]] = []

        for n, (sound, section) in enumerate(zip(sounds, new_sound_sections), start=1):
            section = TimelapseXmlOps.recount_ids(section, (max_id + 1) * n)
            clones += section

            if uid := TimelapseXmlOps.clip_project_item_uid(section):
                panel_uids.append(uid)

            # Only full-template (timeline) sections carry a slot; panel-only ones don't.
            # Keep the slot paired with the sound it was realized from: that pairing is
            # exactly what the layout needs, and it is known here for free.
            if slot_id := TimelapseXmlOps.audio_clip_track_item_id(section):
                timeline_slots.append((slot_id, sound))

        xml.insert(insert_at, clones)
        xml.remove_blocks_by_positions([block.span for block in timeline_template])

        TimelapseSchema._register_in_panel(xml, template_panel_uid, panel_uids)

        return template_slot_id, timeline_slots

    @staticmethod
    def _place_on_timeline(xml: Xml, template_slot_id: str | None, timeline_slots: list[tuple[str, Sound]]) -> None:
        """
        Put the chosen sounds on the audio track: register their slots, then lay out.

        The slots already exist in the document — they co-cloned with their panel clips
        in ``_place_in_panel``. Here we register them on the track (anchored after the
        template's own slot) and line them up back-to-back at their real lengths.

        With no slots there is simply nothing to do, and both steps below are already
        empty-safe, so the caller needs no special case.
        """
        if template_slot_id and timeline_slots:
            TimelapseXmlOps.append_track_items_after(xml, template_slot_id, [slot_id for slot_id, _ in timeline_slots])

        TimelapseSchema._lay_out_timeline(xml, timeline_slots)

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
    def _lay_out_timeline(xml: Xml, timeline_slots: list[tuple[str, Sound]]) -> None:
        """
        Line the timeline sounds up back-to-back at their real lengths.

        Each slot arrives paired with the sound it plays, so there is nothing to look
        up. Each sound's real length comes from ffprobe. The first sound starts at 0,
        the next starts where it ended, and so on. For each slot we set two things:
        where it sits on the track (its Start/End) and how much of the clip plays
        (the AudioClip's OutPoint, reached through the slot's SubClip). Every edit
        is worked out up front, then applied from the end of the document backwards
        so the byte offsets stay valid — which is why the slots cannot be placed one
        at a time: each edit changes lengths and shifts every offset after it.
        """
        document = Document(xml.toplevel_blocks())

        edits: list[tuple[int, int, str]] = []
        cursor = 0

        for slot_id, sound in timeline_slots:
            slot = document.by_ref(AudioClipTrackItem, slot_id)

            if slot is None:
                continue

            duration = sound.duration_ticks
            end = cursor + duration

            # Where the clip sits on the track. It always has an end; it gets a
            # start only once we're past 0 (the first clip has none, matching how
            # the template stores it).
            slot_block = slot.block
            edits.append((*slot_block.span, TimelapseXmlOps.set_slot_position(slot_block.text, cursor or None, end)))

            # How much of the clip plays — the clip reached through the slot's SubClip.
            if (subclip := slot.subclip) and (clip := subclip.clip):
                clip_block = clip.block

                if "<OutPoint>" in clip_block.text:
                    edits.append((*clip_block.span, TimelapseXmlOps.set_out_point(clip_block.text, duration)))

            cursor = end

        xml.replace_ranges(edits)

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
