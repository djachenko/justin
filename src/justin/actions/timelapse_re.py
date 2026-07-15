"""
Regex patterns and builders for Premiere Pro XML.

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

# ---------------------------------------------------------------------------
# Attribute patterns used throughout Premiere Pro XML blocks.
# ---------------------------------------------------------------------------

# Numeric id, unique within a ClassID (i.e. two blocks of different types can share a number).
#   ObjectID="   — attribute name
#   (\d+)        — capture: the id
#   "            — closing quote
_OBJECT_ID_RE = r'ObjectID="(\d+)"'

# Instance UUID, globally unique across the entire project.
#   ObjectUID="   — attribute name
#   ([^"]+)       — capture: the UUID value (any chars except closing quote)
#   "             — closing quote
_OBJECT_UID_RE = r'ObjectUID="([^"]+)"'

# Pointer to another block's UUID (an outgoing uuid reference).
#   ObjectURef="   — attribute name
#   ([^"]+)        — capture: the target UUID
#   "              — closing quote
_OBJECT_UREF_RE = r'ObjectURef="([^"]+)"'

# Pointer to another block's numeric id (an outgoing numeric reference).
#   ObjectRef="   — attribute name
#   (\d+)         — capture: the target id
#   "             — closing quote
_OBJECT_REF_RE = r'ObjectRef="(\d+)"'

# UUID used as an identity — either ObjectUID or ObjectURef — for cloning.
# Matches both in one pass so we can remap every identity in a cloned cluster.
#   Object(?:UID|URef)="   — either attribute name (non-capturing group)
#   ([0-9a-f-]{36})        — capture: 36-char hex UUID
#   "                      — closing quote
_IDENTITY_UUID_RE = r'Object(?:UID|URef)="([0-9a-f-]{36})"'

# UUID in a bare <ID> element (also an identity, also remapped when cloning).
#   <ID>              — opening tag
#   ([0-9a-f-]{36})   — capture: 36-char hex UUID
#   </ID>             — closing tag
_BARE_ID_TAG_RE = r'<ID>([0-9a-f-]{36})</ID>'

# ---------------------------------------------------------------------------
# Structural element patterns.
# ---------------------------------------------------------------------------

# Opening tag of a ClipProjectItem block that carries a panel UUID.
# → Panel
#   <ClipProjectItem   — tag name with trailing space (avoids partial-word matches)
#   _OBJECT_UID_RE     — captures the UUID (see above)
_CLIP_PROJECT_ITEM_UID_RE = r'<ClipProjectItem ' + _OBJECT_UID_RE

# Opening tag of an AudioClipTrackItem block that carries a slot ID.
# → Timeline slot
#   <AudioClipTrackItem   — tag name with trailing space
#   _OBJECT_ID_RE         — captures the numeric ID (see above)
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
# List container patterns — used to find the clip list and track slot lists.
# ---------------------------------------------------------------------------

# The project panel's clip list. re.DOTALL required (content spans multiple lines).
#   <Items Version="\d+">   — opening tag with any version number
#   .*?                     — lazy match of the list content
#   </Items>                — closing tag
_PANEL_ITEMS_BLOCK_RE = r'<Items Version="\d+">.*?</Items>'

# Any self-closing panel item line, with leading whitespace, for pruning stale entries.
# The space after "<Item " is intentional — without it "<Items " would also match.
#   [^\S\n]*   — leading whitespace except newlines (the indentation tabs)
#   <Item      — tag name with trailing space
#   [^/]*      — any attributes (stops before the self-closing slash)
#   />\n       — self-closing tag + newline (consumed so no blank line remains)
_ANY_PANEL_ITEM_LINE_RE = r'[^\S\n]*<Item [^/]*/>\n'

# Any TrackItems container (one per track). re.DOTALL required.
# Unlike _track_items_block_re this matches ALL tracks, not just the one with a given anchor.
#   <TrackItems Version="\d+">   — opening tag with any version number
#   .*?                          — lazy match of the list content
#   </TrackItems>                — closing tag
_ANY_TRACK_ITEMS_BLOCK_RE = r'<TrackItems Version="\d+">.*?</TrackItems>'

# Any self-closing track slot line, with leading whitespace, for pruning stale entries.
# The space after "<TrackItem " is intentional — avoids matching "<TrackItems ".
#   [^\S\n]*      — leading whitespace except newlines
#   <TrackItem    — tag name with trailing space
#   [^/]*         — any attributes
#   />\n          — self-closing tag + newline
_ANY_TRACK_ITEM_LINE_RE = r'[^\S\n]*<TrackItem [^/]*/>\n'

# Track slot line capturing ObjectRef — used when renumbering surviving entries.
# (Compare _TRACK_ITEM_LINE_RE which captures Index instead.)
#   <TrackItem Index="\d+"   — tag + index attribute (any index, not captured)
#   ObjectRef="(\d+)"        — capture: the block ID (preserved during renumber)
#   />                       — self-closing tag
_TRACK_ITEM_OBJECTREF_RE = r'<TrackItem Index="\d+" ObjectRef="(\d+)"/>'

# Opening tag of any block that references its media by UUID (uuid-pointer blocks).
# Used to detect broken references: if the uuid isn't live, the block is stale.
#   <(?:Media|VideoClip|AudioClip|MasterClip)   — any of these tag names (non-capturing)
#   ObjectURef="([^"]+)"                         — capture: the UUID being pointed at
_UUID_REF_TAGS_RE = r'<(?:Media|VideoClip|AudioClip|MasterClip) ObjectURef="([^"]+)"'

# Opening tag of any block that references its parent by numeric id (numeric-pointer blocks).
# Used to detect broken references: if the id isn't live, the block is stale.
#   <(?:SubClip|Source|Content)   — any of these tag names (non-capturing)
#   ObjectRef="(\d+)"             — capture: the numeric id being pointed at
_NUMERIC_REF_TAGS_RE = r'<(?:SubClip|Source|Content) ObjectRef="(\d+)"'

# Top-level block opening: a line starting with exactly one tab followed by a tag.
# The second capture group (space or >) ensures we match a real opening tag, not a bare word.
#   (?m)      — multiline: ^ matches start of each line
#   ^\t       — exactly one leading tab (top-level depth)
#   <(\w+)    — capture group 1: tag name
#   ([ >])    — capture group 2: space (tag has attributes) or > (tag has no attributes)
_TOPLEVEL_BLOCK_START_RE = r'(?m)^\t<(\w+)([ >])'

# ---------------------------------------------------------------------------
# Dynamic pattern builders — embed a runtime value, so can't be plain constants.
# ---------------------------------------------------------------------------

# Panel item entry: <Item Index="N" ObjectURef="uuid"/> inside an <Items> block.
# → Panel
#   <Item Index="   — tag + index attribute
#   (\d+)           — capture: position in the panel list
#   " ObjectURef="  — separator before the clip UUID
#   {uid}           — the specific clip UUID (escaped — UUIDs contain hyphens)
#   "               — closing quote
def _panel_item_re(uid: str) -> str:
    return rf'<Item Index="(\d+)" ObjectURef="{re.escape(uid)}"'


# Slot line in a TrackItems list, with surrounding whitespace, for deletion.
# → Timeline slot
#   [^\S\n]*              — leading whitespace except newlines (the indentation tabs)
#   <TrackItem Index="\d+" — tag with any index (targeting by ID, not by position)
#   " ObjectRef="{id}"    — the specific slot block ID we want to remove
#   />\n                  — self-closing tag + newline (consumed so no blank line remains)
def _track_item_slot_re(track_item_id: str) -> str:
    return rf'[^\S\n]*<TrackItem Index="\d+" ObjectRef="{track_item_id}"/>\n'


# The entire <TrackItems> block that contains a specific anchor slot.
# → Timeline slot
#   <TrackItems Version="\d+">     — opening tag with any version number
#   (?:(?!</TrackItems>).)*?       — lazy match of content before the anchor; negative lookahead
#                                     prevents eating past the first </TrackItems>
#   <TrackItem … ObjectRef="{id}"/> — the anchor slot that identifies this as the audio track
#   .*?                            — lazy match of remaining content (needs re.DOTALL)
#   </TrackItems>                  — closing tag
def _track_items_block_re(anchor_id: str) -> str:
    return (
        rf'<TrackItems Version="\d+">(?:(?!</TrackItems>).)*?'
        rf'<TrackItem Index="\d+" ObjectRef="{anchor_id}"/>.*?</TrackItems>'
    )


# Attribute-scoped id replacement: matches ObjectID="N" or ObjectRef="N" for a specific N.
# Used when cloning blocks to remap numeric ids without touching bare numbers elsewhere.
#   (                          — start capture group 1 (preserved in replacement via \g<1>)
#   (?:ObjectID|ObjectRef)="   — either attribute name (non-capturing alternation)
#   )                          — end capture group 1
#   {old_id}                   — the specific id value (escaped)
#   "                          — closing quote
def _id_remap_re(old_id: str) -> str:
    return rf'((?:ObjectID|ObjectRef)="){re.escape(old_id)}"'
