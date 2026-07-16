import re
import uuid

from justin.actions.timelapse_re import TimelapseRe
from justin.actions.timelapse_xml import Xml


class TimelapseXmlOps:
    """Named regex operations over Premiere Pro XML — queries, block-text edits,
    whole-project edits, and block-cluster operations. All staticmethods; grouped
    here as the domain vocabulary the schema builds on."""

    # -----------------------------------------------------------------------
    # Queries on individual block text
    # -----------------------------------------------------------------------

    @staticmethod
    def block_uid(text: str) -> str | None:
        """
        The ObjectUID of a block — a globally-unique UUID that identifies this specific
        instance. Used for ClipProjectItem blocks: we read the template panel entry's UID
        so we know where to anchor the new entries in the panel list.
        """
        if m := re.search(TimelapseRe.OBJECT_UID, text):
            return m.group(1)
        return None

    @staticmethod
    def clip_project_item_uid(text: str) -> str | None:
        """
        The UUID of a ClipProjectItem inside a cloned block cluster.
        After cloning, we collect this UUID and add an <Item .../> line to the panel
        list so the new clip shows up in the Project panel.
        """
        if m := re.search(TimelapseRe.CLIP_PROJECT_ITEM_UID, text):
            return m.group(1)
        return None

    @staticmethod
    def audio_clip_track_item_id(text: str) -> str | None:
        """
        The numeric ID of an AudioClipTrackItem inside a cloned block cluster.
        After cloning, we collect this ID and add a <TrackItem .../> line to the audio
        track's slot list so the new clip gets a slot on the timeline.
        """
        if m := re.search(TimelapseRe.AUDIO_CLIP_TRACK_ITEM_ID, text):
            return m.group(1)
        return None

    @staticmethod
    def subclip_ref(text: str) -> str | None:
        """
        The numeric ID from a block's <SubClip ObjectRef="N"/> pointer.
        A timeline slot (AudioClipTrackItem) holds a SubClip pointer that names the
        SubClip block carrying this slot's playback settings and display name.
        """
        if m := re.search(TimelapseRe.SUBCLIP_REF, text):
            return m.group(1)
        return None

    @staticmethod
    def clip_ref(text: str) -> str | None:
        """
        The numeric ID from a SubClip's <Clip ObjectRef="N"/> pointer.
        A SubClip points at an AudioClip (or VideoClip) that holds the actual media data.
        Following this chain: slot → SubClip → AudioClip lets us set how much of the
        clip plays (via the AudioClip's OutPoint).
        """
        if m := re.search(TimelapseRe.CLIP_REF, text):
            return m.group(1)
        return None

    @staticmethod
    def block_name(text: str) -> str | None:
        """
        The value inside a block's <Name> element.
        For SubClip blocks this is the filename of the media the clip represents.
        We use it to match a timeline slot back to the sound file it plays.
        """
        if m := re.search(TimelapseRe.BLOCK_NAME, text):
            return m.group(1)
        return None

    @staticmethod
    def video_stream_ref(media_text: str) -> str | None:
        """
        The id of the VideoStream a sound's Media block points at, or None if it has no
        video part. The template's mp4 sound has one; an audio-only file (mp3, wav, …)
        doesn't, so its absence is how we detect "already audio-only, nothing to strip".
        """
        if m := re.search(TimelapseRe.VIDEO_STREAM_REF, media_text):
            return m.group(1)
        return None

    @staticmethod
    def master_clip_slot_ref(master_text: str, index: int) -> str | None:
        """
        The clip id in a MasterClip's slot: index 0 is the video half, index 1 the audio
        half. Used to find each half so the video side can be stripped for audio-only files.
        """
        if m := re.search(TimelapseRe.master_clip_slot(index), master_text):
            return m.group(1)
        return None

    @staticmethod
    def reference_ids(text: str) -> set[str]:
        """Every numeric ObjectRef a block points at — used to compare a clip's sub-blocks."""
        return set(re.findall(TimelapseRe.OBJECT_REF, text))

    # -----------------------------------------------------------------------
    # Block text edits — return modified text, do not touch Xml
    # -----------------------------------------------------------------------

    @staticmethod
    def set_slot_position(slot_text: str, start: int | None, end: int) -> str:
        """
        Rewrite the start/end position of a timeline slot.
        A slot's position on the track is stored as <Start>N</Start><End>N</End>.
        The very first slot (starting at tick 0) has no explicit Start tag — Premiere
        treats the absence of Start as 0. Every later slot has both. We replace
        whatever is currently there with the new position.
        """
        if start is not None:
            new_position = f'<Start>{start}</Start>\n\t\t\t\t<End>{end}</End>'
        else:
            new_position = f'<End>{end}</End>'

        return re.sub(TimelapseRe.SLOT_POSITION, new_position, slot_text, count=1)

    @staticmethod
    def set_out_point(clip_text: str, duration: int) -> str:
        """
        Rewrite an AudioClip's OutPoint to match the sound's actual length.
        OutPoint is how far into the clip playback stops, in Premiere ticks.
        The cloned template block has a placeholder value; we replace it with the
        real duration measured by ffprobe.
        """
        return re.sub(TimelapseRe.OUT_POINT, f'<OutPoint>{duration}</OutPoint>', clip_text, count=1)

    @staticmethod
    def drop_video_stream(media_text: str, stream_id: str) -> str:
        """Remove the VideoStream pointer line from a Media block, leaving it audio-only."""
        return media_text.replace(f'\t\t<VideoStream ObjectRef="{stream_id}"/>\n', '')

    @staticmethod
    def promote_audio_to_first_slot(master_text: str, video_clip_id: str, audio_clip_id: str) -> str:
        """
        Drop a MasterClip's video slot and move its audio clip from slot 1 up to slot 0.
        After the video half is stripped, the MasterClip should list only the audio clip,
        at index 0.
        """
        without_video = master_text.replace(f'\t\t<Clip Index="0" ObjectRef="{video_clip_id}"/>\n', '')

        return without_video.replace(
            f'<Clip Index="1" ObjectRef="{audio_clip_id}"/>',
            f'<Clip Index="0" ObjectRef="{audio_clip_id}"/>',
        )

    # -----------------------------------------------------------------------
    # Whole-project XML edits — mutate Xml in place
    # -----------------------------------------------------------------------

    @staticmethod
    def clear_audio_cache_paths(xml: Xml) -> None:
        """
        Blank the waveform cache paths baked into the template.
        When Premiere saves a project it records absolute on-disk paths to the
        cached waveform (ConformedAudioPath) and peak levels (PeakFilePath) for each
        clip. Those paths belong to the template author's machine. Blanking them tells
        Premiere to regenerate the caches for our sounds instead of trusting stale data.
        """
        xml.sub(TimelapseRe.CONFORMED_AUDIO_PATH, '<ConformedAudioPath></ConformedAudioPath>')
        xml.sub(TimelapseRe.PEAK_FILE_PATH, '<PeakFilePath></PeakFilePath>')

    @staticmethod
    def remove_track_item_lines(xml: Xml, track_item_ids: list[str]) -> None:
        """
        Strike the given slots from the audio track's slot list.
        The track's <TrackItems> element lists one self-closing line per slot:
            <TrackItem Index="2" ObjectRef="57"/>
        We delete those lines for every ID in the list. The slot blocks themselves
        are removed separately via remove_blocks_by_positions.
        """
        for track_item_id in track_item_ids:
            xml.sub(TimelapseRe.track_item_slot(track_item_id), '')

    @staticmethod
    def append_track_items_after(xml: Xml, anchor_id: str, new_ids: list[str]) -> None:
        """
        Append new timeline slots to the audio track's slot list, right after an anchor slot.

        There's one <TrackItems> list per track (audio and video each have their own).
        We find the right one — the audio track's — by locating the list that already
        contains the anchor slot (the template sound's slot). Then we append the new
        slot references after the last existing entry, continuing the Index sequence.
        """
        def rewrite(track_items_block: re.Match) -> str:
            listing = track_items_block.group(0)
            existing = list(re.finditer(TimelapseRe.TRACK_ITEM_LINE, listing))
            last_index = int(existing[-1].group(1))
            added = "".join(
                f'\n\t\t\t\t\t<TrackItem Index="{last_index + offset}" ObjectRef="{new_id}"/>'
                for offset, new_id in enumerate(new_ids, start=1)
            )
            return listing.replace(existing[-1].group(0), existing[-1].group(0) + added, 1)

        xml.sub(TimelapseRe.track_items_block(anchor_id), rewrite, count=1, flags=re.DOTALL)

    # -----------------------------------------------------------------------
    # Integration — assign fresh, non-clashing ids to a realized section
    # -----------------------------------------------------------------------

    @staticmethod
    def recount_ids(section: str, id_offset: int) -> str:
        """
        Give a sound section fresh identities so it can coexist in the document.

        A realized section still carries the template's original ids, shared with
        every other section realized from the same template. To integrate them all,
        each gets a distinct id-space:
          * every plain-number id is bumped by ``id_offset`` (picked bigger than any
            id already in use, so the bumped numbers can't clash);
          * every uuid identity (ObjectUID / ObjectURef, and the ``<ID>`` codes) is
            replaced with a brand-new uuid.

        Ids are pure integration — this is where they get assigned, nowhere else.
        One remap over the whole section keeps its internal cross-references
        consistent (e.g. a timeline slot's pointer to its own panel MasterClip).

        What we must NOT touch is ClassID (and ESP.PresetGuid). Those look like uuids
        too, but they aren't identities — they say *what kind* of chunk this is, and
        every chunk of a kind shares the same one. Change those and Premiere no
        longer recognises the chunk's type and silently refuses to open the file.
        (This was the bug that made multi-sound projects fail to open.)
        """
        numeric_ids = sorted(set(re.findall(TimelapseRe.OBJECT_ID, section)), key=int)
        id_remap = {old: str(int(old) + id_offset) for old in numeric_ids}

        # Collect uuids used as identities: ObjectUID/ObjectURef attributes and bare <ID> tags.
        # These are 36-char hex strings like "a1b2c3d4-…". ClassID looks the same but is NOT
        # an identity — it names the chunk's type and must not be touched.
        identity_uids = set(re.findall(TimelapseRe.IDENTITY_UUID, section))
        identity_uids |= set(re.findall(TimelapseRe.BARE_ID_TAG, section))
        uid_remap = {old: str(uuid.uuid4()) for old in identity_uids}

        # TimelapseRe.id_remap(old_id) scopes the swap to ObjectID="N"/ObjectRef="N",
        # so bare numbers elsewhere (e.g. inside a Name) are left untouched.
        for old_id, new_id in id_remap.items():
            section = re.sub(TimelapseRe.id_remap(old_id), rf'\g<1>{new_id}"', section)

        for old_uid, new_uid in uid_remap.items():
            section = section.replace(old_uid, new_uid)

        return section
