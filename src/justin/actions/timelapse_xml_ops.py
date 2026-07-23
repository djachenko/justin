import re
import uuid

from justin.actions.timelapse_re import TimelapseRe, search_group
from justin.actions.timelapse_xml import Xml


class TimelapseXmlOps:
    """Regex operations that have no single block to belong to.

    What is left here works on the *whole* document, or on a freshly cloned section
    that is not part of one yet — neither has an owner in the typed model, so it
    stays a named operation over text.

    Anything that did belong to one block now lives on its model class instead
    (``Clip.trimmed_to``, ``AudioClipTrackItem.placed_at``, ``Media`` and
    ``MasterClip``'s ``without_*``) — see timelapse_model.
    """

    # -----------------------------------------------------------------------
    # Queries on a cloned section, before it becomes part of a document
    # -----------------------------------------------------------------------

    @staticmethod
    def block_uid(text: str) -> str | None:
        """
        The ObjectUID of a block — a globally-unique UUID that identifies this specific
        instance. Used for ClipProjectItem blocks: we read the template panel entry's UID
        so we know where to anchor the new entries in the panel list.
        """
        return search_group(TimelapseRe.OBJECT_UID, text)

    @staticmethod
    def clip_project_item_uid(text: str) -> str | None:
        """
        The UUID of a ClipProjectItem inside a cloned block cluster.
        After cloning, we collect this UUID and add an <Item .../> line to the panel
        list so the new clip shows up in the Project panel.
        """
        return search_group(TimelapseRe.CLIP_PROJECT_ITEM_UID, text)

    @staticmethod
    def audio_clip_track_item_id(text: str) -> str | None:
        """
        The numeric ID of an AudioClipTrackItem inside a cloned block cluster.
        After cloning, we collect this ID and add a <TrackItem .../> line to the audio
        track's slot list so the new clip gets a slot on the timeline.
        """
        return search_group(TimelapseRe.AUDIO_CLIP_TRACK_ITEM_ID, text)



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
