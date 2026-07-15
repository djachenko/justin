"""
Named operations on Premiere Pro XML.

Every function here wraps one or more regex so that call sites in timelapse_prproj.py
read as intent — what we're looking for and why — rather than as bare patterns.

Premiere XML concepts used throughout:

  Panel            The "Project" panel in the Premiere UI: the left-side list of every
                   clip in the project. Each entry is a ClipProjectItem block with a
                   globally-unique UUID (ObjectUID). The panel's XML element is <Items>;
                   each entry inside it is a self-closing <Item Index="N" ObjectURef="uuid"/>.

  Timeline slot    One placed instance of a clip on the audio track; stored as an
                   AudioClipTrackItem block with a numeric ID (ObjectID). The track's slot
                   list is <TrackItems>; each entry is <TrackItem Index="N" ObjectRef="id"/>.

  SubClip          The bridge between a timeline slot and its underlying media. A slot's
                   block carries <SubClip ObjectRef="N"/> pointing at a SubClip block; the
                   SubClip block carries the clip's display Name and a <Clip ObjectRef="N"/>
                   pointer to the AudioClip (or VideoClip) with the actual media data.

  OutPoint         How far into a clip playback stops, in Premiere ticks. The AudioClip
                   block stores this as <OutPoint>N</OutPoint>. The template has a placeholder
                   value; we replace it with the real duration from ffprobe.

  ConformedAudioPath / PeakFilePath
                   Absolute paths where Premiere cached the waveform and peak levels for a
                   clip, on the machine where the project was last saved. Meaningless on any
                   other machine — we blank them so Premiere rebuilds the caches for our sounds.
"""

import re

from justin.actions.timelapse_re import _OBJECT_ID_RE, _OBJECT_UID_RE
from justin.actions.timelapse_xml import Xml


# ---------------------------------------------------------------------------
# Regex constants
# Each one matches a specific structural element of the Premiere XML.
# ---------------------------------------------------------------------------

# Opening tag of a ClipProjectItem block that carries a panel UUID.
# → Panel
#   <ClipProjectItem   — tag name with trailing space (avoids partial-word matches)
#   _OBJECT_UID_RE     — captures the UUID (see timelapse_re)
_CLIP_PROJECT_ITEM_UID_RE = r'<ClipProjectItem ' + _OBJECT_UID_RE

# Opening tag of an AudioClipTrackItem block that carries a slot ID.
# → Timeline slot
#   <AudioClipTrackItem   — tag name with trailing space
#   _OBJECT_ID_RE         — captures the numeric ID (see timelapse_re)
_AUDIO_CLIP_TRACK_ITEM_ID_RE = r'<AudioClipTrackItem ' + _OBJECT_ID_RE

# The SubClip pointer inside any block that references one.
# → SubClip
#   <SubClip ObjectRef="   — tag name + attribute prefix
#   (\d+)                  — capture: numeric ID of the SubClip being pointed at
#   "                      — closing quote; tag stays open, we only need the id
_SUBCLIP_REF_RE = r'<SubClip ObjectRef="(\d+)"'

# The Clip pointer inside a SubClip block.
# → SubClip
#   <Clip ObjectRef="   — tag name + attribute prefix
#   (\d+)               — capture: numeric ID of the AudioClip (or VideoClip)
#   "                   — closing quote
_CLIP_REF_RE = r'<Clip ObjectRef="(\d+)"'

# The Name element in any block (typically a SubClip carries the filename here).
# → SubClip
#   <Name>      — opening tag
#   ([^<]+)     — capture: any characters that aren't a tag opener (stops at </Name>)
#   </Name>     — closing tag
_BLOCK_NAME_RE = r'<Name>([^<]+)</Name>'

# The Start/End position pair of a timeline slot. Start is optional: the very
# first slot (at tick 0) has no Start element — Premiere treats its absence as 0.
# → Timeline slot
#   (?:<Start>\d+</Start>\n\t+)?   — optional Start element followed by a newline + indentation
#   <End>\d+</End>                 — mandatory End element
_SLOT_POSITION_RE = r'(?:<Start>\d+</Start>\n\t+)?<End>\d+</End>'

# The OutPoint element inside an AudioClip block.
# → OutPoint
#   <OutPoint>   — opening tag
#   \d+          — tick count (Premiere ticks, not seconds)
#   </OutPoint>  — closing tag
_OUT_POINT_RE = r'<OutPoint>\d+</OutPoint>'

# The ConformedAudioPath element — an absolute path to the cached waveform file.
# → ConformedAudioPath / PeakFilePath
#   <ConformedAudioPath>   — opening tag
#   [^<]+                  — the path (any characters except a tag opener)
#   </ConformedAudioPath>  — closing tag
_CONFORMED_AUDIO_PATH_RE = r'<ConformedAudioPath>[^<]+</ConformedAudioPath>'

# The PeakFilePath element — an absolute path to the cached peak levels file.
# → ConformedAudioPath / PeakFilePath
#   <PeakFilePath>   — opening tag
#   [^<]+            — the path
#   </PeakFilePath>  — closing tag
_PEAK_FILE_PATH_RE = r'<PeakFilePath>[^<]+</PeakFilePath>'

# A single self-closing slot entry inside a TrackItems list.
# → Timeline slot
#   <TrackItem Index="   — tag name + index attribute
#   (\d+)                — capture: position in the list (used to continue the sequence)
#   " ObjectRef="        — separator before the block reference
#   \d+                  — numeric ID of the AudioClipTrackItem block (not captured)
#   "/>                  — self-closing tag
_TRACK_ITEM_LINE_RE = r'<TrackItem Index="(\d+)" ObjectRef="\d+"/>'


# ---------------------------------------------------------------------------
# Dynamic pattern builders — can't be plain constants because they embed a
# runtime value; returned as strings for use with re.search / re.sub / xml.sub.
# ---------------------------------------------------------------------------

def _panel_item_re(uid: str) -> str:
    """
    Pattern matching the panel entry for a specific clip UUID.
    → Panel

    The Project panel's <Items> list looks like:
        <Item Index="3" ObjectURef="a1b2-…"/>
        <Item Index="4" ObjectURef="c3d4-…"/>

    Pattern breakdown:
      <Item Index="    — tag opening + index attribute
      (\\d+)           — capture: position in the list; used to anchor new entries after this one
      " ObjectURef="   — separator before the UUID attribute
      {uid}            — the specific clip UUID (re.escape handles the hyphens)
      "                — closing quote
    """
    return rf'<Item Index="(\d+)" ObjectURef="{re.escape(uid)}"'


def _track_item_slot_re(track_item_id: str) -> str:
    """
    Pattern matching a specific slot line in a track's slot list, including its
    surrounding whitespace, so deleting the match leaves no blank line behind.
    → Timeline slot

    A TrackItems list looks like:
        \t\t\t\t\t<TrackItem Index="0" ObjectRef="42"/>
        \t\t\t\t\t<TrackItem Index="1" ObjectRef="57"/>

    Pattern breakdown:
      [^\\S\\n]*            — leading whitespace except newlines (the indentation tabs)
      <TrackItem Index="\\d+" — tag with any index number (we're targeting by ID, not index)
      ObjectRef="{id}"      — the specific slot block ID we want to remove
      />                    — self-closing tag
      \n                    — trailing newline, consumed so no blank line is left
    """
    return rf'[^\S\n]*<TrackItem Index="\d+" ObjectRef="{track_item_id}"/>\n'


def _track_items_block_re(anchor_id: str) -> str:
    """
    Pattern matching the entire <TrackItems> block that contains a specific anchor slot.
    → Timeline slot

    Each track (audio, video) has its own <TrackItems> block. We identify the audio
    track's block by finding the one that already contains the anchor slot (the template
    sound's slot). The match spans the whole block so the rewrite callback can append
    to the end of it.

    Pattern breakdown:
      <TrackItems Version="\\d+">    — opening tag with any version number
      (?:(?!</TrackItems>).)*?       — lazy match of everything that is NOT the closing tag
                                       (negative lookahead prevents eating past the first </TrackItems>)
      <TrackItem … ObjectRef="{id}"/> — the specific anchor slot that identifies this block
      .*?                            — lazy match of remaining content (needs re.DOTALL)
      </TrackItems>                  — closing tag
    """
    return (
        rf'<TrackItems Version="\d+">(?:(?!</TrackItems>).)*?'
        rf'<TrackItem Index="\d+" ObjectRef="{anchor_id}"/>.*?</TrackItems>'
    )


# ---------------------------------------------------------------------------
# Queries on individual block text
# ---------------------------------------------------------------------------

def block_uid(text: str) -> str | None:
    """
    The ObjectUID of a block — a globally-unique UUID that identifies this specific
    instance. Used for ClipProjectItem blocks: we read the template panel entry's UID
    so we know where to anchor the new entries in the panel list.
    """
    if m := re.search(_OBJECT_UID_RE, text):
        return m.group(1)
    return None


def clip_project_item_uid(text: str) -> str | None:
    """
    The UUID of a ClipProjectItem inside a cloned block cluster.
    After cloning, we collect this UUID and add an <Item .../> line to the panel
    list so the new clip shows up in the Project panel.
    """
    if m := re.search(_CLIP_PROJECT_ITEM_UID_RE, text):
        return m.group(1)
    return None


def audio_clip_track_item_id(text: str) -> str | None:
    """
    The numeric ID of an AudioClipTrackItem inside a cloned block cluster.
    After cloning, we collect this ID and add a <TrackItem .../> line to the audio
    track's slot list so the new clip gets a slot on the timeline.
    """
    if m := re.search(_AUDIO_CLIP_TRACK_ITEM_ID_RE, text):
        return m.group(1)
    return None


def subclip_ref(text: str) -> str | None:
    """
    The numeric ID from a block's <SubClip ObjectRef="N"/> pointer.
    A timeline slot (AudioClipTrackItem) holds a SubClip pointer that names the
    SubClip block carrying this slot's playback settings and display name.
    """
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
    if m := re.search(_CLIP_REF_RE, text):
        return m.group(1)
    return None


def block_name(text: str) -> str | None:
    """
    The value inside a block's <Name> element.
    For SubClip blocks this is the filename of the media the clip represents.
    We use it to match a timeline slot back to the sound file it plays.
    """
    if m := re.search(_BLOCK_NAME_RE, text):
        return m.group(1)
    return None


# ---------------------------------------------------------------------------
# Queries on the whole project XML
# ---------------------------------------------------------------------------

def max_object_id(xml: Xml) -> int:
    """
    The highest numeric ObjectID currently in the project.
    When cloning a block cluster, new IDs must all be above this number so they
    can't accidentally collide with anything already in the file.
    """
    return max(int(i) for i in re.findall(_OBJECT_ID_RE, xml.raw))


def find_panel_item_index(xml: Xml, uid: str) -> int | None:
    """
    The Index of the panel entry that points at the given UUID.
    The Project panel's <Items> list contains self-closing lines like
    <Item Index="3" ObjectURef="some-uuid"/>. We locate the entry by UUID so we
    know which Index to anchor new entries after when registering cloned clips.
    """
    if m := re.search(_panel_item_re(uid), xml.raw):
        return int(m.group(1))

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
    xml.sub(_CONFORMED_AUDIO_PATH_RE, '<ConformedAudioPath></ConformedAudioPath>')
    xml.sub(_PEAK_FILE_PATH_RE, '<PeakFilePath></PeakFilePath>')


def remove_track_item_lines(xml: Xml, track_item_ids: list[str]) -> None:
    """
    Strike the given slots from the audio track's slot list.
    The track's <TrackItems> element lists one self-closing line per slot:
        <TrackItem Index="2" ObjectRef="57"/>
    We delete those lines for every ID in the list. The slot blocks themselves
    are removed separately via remove_blocks_by_positions.
    """
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
    def rewrite(track_items_block: re.Match) -> str:
        listing = track_items_block.group(0)
        existing = list(re.finditer(_TRACK_ITEM_LINE_RE, listing))
        last_index = int(existing[-1].group(1))
        added = "".join(
            f'\n\t\t\t\t\t<TrackItem Index="{last_index + offset}" ObjectRef="{new_id}"/>'
            for offset, new_id in enumerate(new_ids, start=1)
        )
        return listing.replace(existing[-1].group(0), existing[-1].group(0) + added, 1)

    xml.sub(_track_items_block_re(anchor_id), rewrite, count=1, flags=re.DOTALL)
