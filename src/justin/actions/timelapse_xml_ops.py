import re
import uuid

from justin.actions.timelapse_block import Block
from justin.actions.timelapse_re import (
    _OBJECT_ID_RE,
    _OBJECT_UID_RE,
    _OBJECT_UREF_RE,
    _OBJECT_REF_RE,
    _IDENTITY_UUID_RE,
    _BARE_ID_TAG_RE,
    _CLIP_PROJECT_ITEM_UID_RE,
    _AUDIO_CLIP_TRACK_ITEM_ID_RE,
    _SUBCLIP_REF_RE,
    _CLIP_REF_RE,
    _BLOCK_NAME_RE,
    _SLOT_POSITION_RE,
    _OUT_POINT_RE,
    _CONFORMED_AUDIO_PATH_RE,
    _PEAK_FILE_PATH_RE,
    _TRACK_ITEM_LINE_RE,
    _track_item_slot_re,
    _track_items_block_re,
    _id_remap_re,
)
from justin.actions.timelapse_xml import Xml, _CLIP_MEDIA_TYPES


# ---------------------------------------------------------------------------
# Queries on individual block text
# ---------------------------------------------------------------------------

def block_uid(text: str) -> str | None:
    """
    The ObjectUID of a block — a globally-unique UUID that identifies this specific
    instance. Used for ClipProjectItem blocks: we read the template panel entry's UID
    so we know where to anchor the new entries in the panel list.
    """
    # _OBJECT_UID_RE: ObjectUID="([^"]+)"
    #   ObjectUID="   — attribute name
    #   ([^"]+)       — capture: the UUID value (any chars except closing quote)
    #   "             — closing quote
    if m := re.search(_OBJECT_UID_RE, text):
        return m.group(1)
    return None


def clip_project_item_uid(text: str) -> str | None:
    """
    The UUID of a ClipProjectItem inside a cloned block cluster.
    After cloning, we collect this UUID and add an <Item .../> line to the panel
    list so the new clip shows up in the Project panel.
    """
    # _CLIP_PROJECT_ITEM_UID_RE: <ClipProjectItem ObjectUID="([^"]+)"
    #   <ClipProjectItem   — tag name with trailing space (avoids partial-word matches)
    #   ObjectUID="        — attribute name
    #   ([^"]+)            — capture: the panel UUID
    #   "                  — closing quote
    if m := re.search(_CLIP_PROJECT_ITEM_UID_RE, text):
        return m.group(1)
    return None


def audio_clip_track_item_id(text: str) -> str | None:
    """
    The numeric ID of an AudioClipTrackItem inside a cloned block cluster.
    After cloning, we collect this ID and add a <TrackItem .../> line to the audio
    track's slot list so the new clip gets a slot on the timeline.
    """
    # _AUDIO_CLIP_TRACK_ITEM_ID_RE: <AudioClipTrackItem ObjectID="(\d+)"
    #   <AudioClipTrackItem   — tag name with trailing space
    #   ObjectID="            — attribute name
    #   (\d+)                 — capture: the numeric slot ID
    #   "                     — closing quote
    if m := re.search(_AUDIO_CLIP_TRACK_ITEM_ID_RE, text):
        return m.group(1)
    return None


def subclip_ref(text: str) -> str | None:
    """
    The numeric ID from a block's <SubClip ObjectRef="N"/> pointer.
    A timeline slot (AudioClipTrackItem) holds a SubClip pointer that names the
    SubClip block carrying this slot's playback settings and display name.
    """
    # _SUBCLIP_REF_RE: <SubClip ObjectRef="(\d+)"
    #   <SubClip ObjectRef="   — tag name + attribute prefix
    #   (\d+)                  — capture: numeric ID of the SubClip
    #   "                      — closing quote
    if m := re.search(_SUBCLIP_REF_RE, text):
        return m.group(1)
    return None


def clip_ref(text: str) -> str | None:
    """
    The numeric ID from a SubClip's <Clip ObjectRef="N"/> pointer.
    A SubClip points at an AudioClip (or VideoClip) that holds the actual media data.
    Following this chain: slot → SubClip → AudioClip lets us set how much of the
    clip plays (via the AudioClip's OutPoint).
    """
    # _CLIP_REF_RE: <Clip ObjectRef="(\d+)"
    #   <Clip ObjectRef="   — tag name + attribute prefix
    #   (\d+)               — capture: numeric ID of the AudioClip (or VideoClip)
    #   "                   — closing quote
    if m := re.search(_CLIP_REF_RE, text):
        return m.group(1)
    return None


def block_name(text: str) -> str | None:
    """
    The value inside a block's <Name> element.
    For SubClip blocks this is the filename of the media the clip represents.
    We use it to match a timeline slot back to the sound file it plays.
    """
    # _BLOCK_NAME_RE: <Name>([^<]+)</Name>
    #   <Name>      — opening tag
    #   ([^<]+)     — capture: any characters that aren't a tag opener (stops at </Name>)
    #   </Name>     — closing tag
    if m := re.search(_BLOCK_NAME_RE, text):
        return m.group(1)
    return None


# ---------------------------------------------------------------------------
# Block text edits — return modified text, do not touch Xml
# ---------------------------------------------------------------------------

def set_slot_position(slot_text: str, start: int | None, end: int) -> str:
    """
    Rewrite the start/end position of a timeline slot.
    A slot's position on the track is stored as <Start>N</Start><End>N</End>.
    The very first slot (starting at tick 0) has no explicit Start tag — Premiere
    treats the absence of Start as 0. Every later slot has both. We replace
    whatever is currently there with the new position.
    """
    # _SLOT_POSITION_RE: (?:<Start>\d+</Start>\n\t+)?<End>\d+</End>
    #   (?:<Start>\d+</Start>\n\t+)?   — optional Start element + newline + indentation
    #   <End>\d+</End>                 — mandatory End element
    if start is not None:
        new_position = f'<Start>{start}</Start>\n\t\t\t\t<End>{end}</End>'
    else:
        new_position = f'<End>{end}</End>'

    return re.sub(_SLOT_POSITION_RE, new_position, slot_text, count=1)


def set_out_point(clip_text: str, duration: int) -> str:
    """
    Rewrite an AudioClip's OutPoint to match the sound's actual length.
    OutPoint is how far into the clip playback stops, in Premiere ticks.
    The cloned template block has a placeholder value; we replace it with the
    real duration measured by ffprobe.
    """
    # _OUT_POINT_RE: <OutPoint>\d+</OutPoint>
    #   <OutPoint>   — opening tag
    #   \d+          — tick count (Premiere ticks, not seconds)
    #   </OutPoint>  — closing tag
    return re.sub(_OUT_POINT_RE, f'<OutPoint>{duration}</OutPoint>', clip_text, count=1)


# ---------------------------------------------------------------------------
# Whole-project XML edits — mutate Xml in place
# ---------------------------------------------------------------------------

def clear_audio_cache_paths(xml: Xml) -> None:
    """
    Blank the waveform cache paths baked into the template.
    When Premiere saves a project it records absolute on-disk paths to the
    cached waveform (ConformedAudioPath) and peak levels (PeakFilePath) for each
    clip. Those paths belong to the template author's machine. Blanking them tells
    Premiere to regenerate the caches for our sounds instead of trusting stale data.
    """
    # _CONFORMED_AUDIO_PATH_RE: <ConformedAudioPath>[^<]+</ConformedAudioPath>
    #   <ConformedAudioPath>   — opening tag
    #   [^<]+                  — the path (any chars except a tag opener)
    #   </ConformedAudioPath>  — closing tag
    xml.sub(_CONFORMED_AUDIO_PATH_RE, '<ConformedAudioPath></ConformedAudioPath>')
    # _PEAK_FILE_PATH_RE: <PeakFilePath>[^<]+</PeakFilePath>
    #   <PeakFilePath>   — opening tag
    #   [^<]+            — the path
    #   </PeakFilePath>  — closing tag
    xml.sub(_PEAK_FILE_PATH_RE, '<PeakFilePath></PeakFilePath>')


def remove_track_item_lines(xml: Xml, track_item_ids: list[str]) -> None:
    """
    Strike the given slots from the audio track's slot list.
    The track's <TrackItems> element lists one self-closing line per slot:
        <TrackItem Index="2" ObjectRef="57"/>
    We delete those lines for every ID in the list. The slot blocks themselves
    are removed separately via remove_blocks_by_positions.
    """
    # _track_item_slot_re(id): [^\S\n]*<TrackItem Index="\d+" ObjectRef="{id}"/>\n
    #   [^\S\n]*            — leading whitespace except newlines (the indentation tabs)
    #   <TrackItem Index="  — tag name + index attribute (any index — targeting by ID)
    #   \d+"                — index number + closing quote
    #   ObjectRef="{id}"    — the specific slot ID we want to remove
    #   />\n                — self-closing tag + newline (consumed so no blank line remains)
    for track_item_id in track_item_ids:
        xml.sub(_track_item_slot_re(track_item_id), '')


def append_track_items_after(xml: Xml, anchor_id: str, new_ids: list[str]) -> None:
    """
    Append new timeline slots to the audio track's slot list, right after an anchor slot.

    There's one <TrackItems> list per track (audio and video each have their own).
    We find the right one — the audio track's — by locating the list that already
    contains the anchor slot (the template sound's slot). Then we append the new
    slot references after the last existing entry, continuing the Index sequence.
    """
    # _track_items_block_re(id): <TrackItems Version="\d+">…<TrackItem … ObjectRef="{id}"/>…</TrackItems>
    #   <TrackItems Version="\d+">    — opening tag with any version number
    #   (?:(?!</TrackItems>).)*?      — lazy match of content before the anchor (negative lookahead
    #                                    prevents eating past the first </TrackItems>)
    #   <TrackItem … ObjectRef="{id}"/> — the anchor slot that identifies this as the audio track
    #   .*?                           — lazy match of remaining content (re.DOTALL)
    #   </TrackItems>                 — closing tag
    def rewrite(track_items_block: re.Match) -> str:
        listing = track_items_block.group(0)
        # _TRACK_ITEM_LINE_RE: <TrackItem Index="(\d+)" ObjectRef="\d+"/>
        #   <TrackItem Index="   — tag name + index attribute
        #   (\d+)                — capture: current position in the list
        #   " ObjectRef="\d+"   — block reference (not captured)
        #   />                   — self-closing tag
        existing = list(re.finditer(_TRACK_ITEM_LINE_RE, listing))
        last_index = int(existing[-1].group(1))
        added = "".join(
            f'\n\t\t\t\t\t<TrackItem Index="{last_index + offset}" ObjectRef="{new_id}"/>'
            for offset, new_id in enumerate(new_ids, start=1)
        )
        return listing.replace(existing[-1].group(0), existing[-1].group(0) + added, 1)

    xml.sub(_track_items_block_re(anchor_id), rewrite, count=1, flags=re.DOTALL)


# ---------------------------------------------------------------------------
# Block cluster operations — work on lists of Block, not on Xml
# ---------------------------------------------------------------------------

def collect_sound_closure(blocks: list[Block], entry_idxs: list[int]) -> list[int]:
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
        own_id = re.search(_OBJECT_ID_RE, block.header)

        if own_id and block.tag in _CLIP_MEDIA_TYPES:
            media_idxs_by_id.setdefault(own_id.group(1), []).append(idx)

        own_uid = re.search(_OBJECT_UID_RE, block.header)

        if own_uid:
            idx_by_uid[own_uid.group(1)] = idx

    reached = set(entry_idxs)
    frontier = list(entry_idxs)

    while frontier:
        block = blocks[frontier.pop()]

        for ref in re.finditer(_OBJECT_REF_RE, block.text):
            for target in media_idxs_by_id.get(ref.group(1), []):
                if target not in reached:
                    reached.add(target)
                    frontier.append(target)

        for uref in re.finditer(_OBJECT_UREF_RE, block.text):
            target = idx_by_uid.get(uref.group(1))

            if target is None:
                continue
            if blocks[target].tag not in _CLIP_MEDIA_TYPES:
                continue
            if target in reached:
                continue

            reached.add(target)
            frontier.append(target)

    return sorted(reached)


def clone_sound_blocks(blocks: list[Block], old_name: str, new_name: str, id_offset: int) -> str:
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

    numeric_ids = sorted(set(re.findall(_OBJECT_ID_RE, combined)), key=int)
    id_remap = {old: str(int(old) + id_offset) for old in numeric_ids}

    # Collect uuids used as identities: ObjectUID/ObjectURef attributes and bare <ID> tags.
    # These are 36-char hex strings like "a1b2c3d4-…". ClassID looks the same but is NOT
    # an identity — it names the chunk's type and must not be touched.
    identity_uids = set(re.findall(_IDENTITY_UUID_RE, combined))
    identity_uids |= set(re.findall(_BARE_ID_TAG_RE, combined))
    uid_remap = {old: str(uuid.uuid4()) for old in identity_uids}

    clone = combined.replace(old_name, new_name)
    # _id_remap_re(old_id): ((?:ObjectID|ObjectRef)="){old_id}"
    #   ((?:ObjectID|ObjectRef)=")   — capture group 1: attribute name + opening quote
    #                                   (preserved in replacement via \g<1>)
    #   {old_id}                     — the specific id value (escaped)
    #   "                            — closing quote
    for old_id, new_id in id_remap.items():
        clone = re.sub(_id_remap_re(old_id), rf'\g<1>{new_id}"', clone)

    for old_uid, new_uid in uid_remap.items():
        clone = clone.replace(old_uid, new_uid)

    return clone
