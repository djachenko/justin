import gzip
import re
import uuid
from pathlib import Path
from typing import Self, NamedTuple

# Attribute patterns used throughout Premiere Pro XML blocks.
_OBJECT_ID_RE = r'ObjectID="(\d+)"'        # numeric id, unique within ClassID
_OBJECT_UID_RE = r'ObjectUID="([^"]+)"'    # instance uuid, globally unique
_OBJECT_UREF_RE = r'ObjectURef="([^"]+)"'  # pointer to another block's uuid
_OBJECT_REF_RE = r'ObjectRef="(\d+)"'      # pointer to another block's numeric id

# UUID patterns used when cloning blocks to a fresh identity.
_IDENTITY_UUID_RE = r'Object(?:UID|URef)="([0-9a-f-]{36})"'  # instance uuid in any ObjectUID/URef attr
_BARE_ID_TAG_RE = r'<ID>([0-9a-f-]{36})</ID>'                 # uuid in a bare <ID> element


class Block(NamedTuple):
    """One chunk of the project, and where it sits in the raw text.

    ``text`` is the chunk's full ``<Tag ...>...</Tag>`` snippet. ``start`` and
    ``end`` are where that snippet begins and ends in the whole file, so we can
    cut it out or drop it back in by slicing the string at those positions.
    """
    # ObjectID / ObjectUID always sit in the opening tag — the very first line.
    # ~110 chars; 120 comfortably covers the longest opening tags we've seen.
    # Example: \t<MasterClip ObjectID="42" ObjectUID="a1b2c3d4-…" ClassID="be4a3c7e-…">
    _HEADER_LEN = 120

    start: int
    end: int
    tag: str
    text: str

    @property
    def header(self) -> str:
        return self.text[:self._HEADER_LEN]


def block_id(block: Block) -> str | None:
    """Numeric ObjectID from the block's opening tag, or None if it has none."""
    m = re.search(_OBJECT_ID_RE, block.header)
    return m.group(1) if m else None


class Xml:
    def __init__(self, xml: str):
        super().__init__()

        self._xml = xml

    @classmethod
    def from_prproj(cls, path: Path) -> Self:
        with gzip.open(path, 'rb') as f:
            xml = f.read().decode('utf-8')

        return cls(xml)

    def to_prproj(self, path: Path) -> None:
        with gzip.open(path, 'wb') as f:
            f.write(self._xml.encode('utf-8'))

    def replace(self, old: str, new: str) -> None:
        self._xml = self._xml.replace(old, new)

    def replace_range(self, start: int, end: int, text: str) -> None:
        self._xml = self._xml[:start] + text + self._xml[end:]

    def insert(self, position: int, text: str) -> None:
        self.replace_range(position, position, text)

    def sub(self, pattern: str, repl, count: int = 0, flags: int = 0) -> None:
        self._xml = re.sub(pattern, repl, self._xml, count=count, flags=flags)

    def remove_blocks_by_positions(self, positions: list[tuple[int, int]]) -> Self:
        # Cut from the end backwards so earlier positions don't shift after each cut.
        for start, end in sorted(positions, reverse=True):
            self._xml = self._xml[:start] + self._xml[end:]

        return self

    def remove_dangling_refs(self) -> Self:
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
            # Collect all ids/uuids that actually exist right now.
            live_uids = set(re.findall(_OBJECT_UID_RE, self._xml))
            live_ids = set(re.findall(_OBJECT_ID_RE, self._xml))

            def prune_panel_items(items_block: re.Match) -> str:
                def keep(item: re.Match) -> str:
                    # Each <Item .../> line points at a clip by uuid. Drop the line if that clip is gone.
                    uref = re.search(_OBJECT_UREF_RE, item.group(0))

                    if uref and uref.group(1) not in live_uids:
                        return ''

                    return item.group(0)

                # Match any self-closing <Item .../> line (with optional leading spaces).
                # The space after "<Item " is intentional — without it the pattern would also
                # match "<Items " and eat the list's own opening tag.
                return re.sub(r'[^\S\n]*<Item [^/]*/>\n', keep, items_block.group(0))

            # Find every <Items>…</Items> block (the project panel's clip list) and prune it.
            self._xml = re.sub(r'<Items Version="\d+">.*?</Items>', prune_panel_items, self._xml, flags=re.DOTALL)

            def prune_track_items(track_items_block: re.Match) -> str:
                def keep(item: re.Match) -> str:
                    # Each <TrackItem .../> line points at a clip by number. Drop if that clip is gone.
                    ref = re.search(_OBJECT_REF_RE, item.group(0))
                    if ref and ref.group(1) not in live_ids:
                        return ''
                    return item.group(0)

                # Same trap: "<TrackItem " needs the space so it doesn't match "<TrackItems ".
                block = re.sub(r'[^\S\n]*<TrackItem [^/]*/>\n', keep, track_items_block.group(0))
                # After dropping entries the Index attributes have gaps; renumber them 0, 1, 2, …
                surviving = list(re.finditer(r'<TrackItem Index="\d+" ObjectRef="(\d+)"/>', block))

                for new_index, item in enumerate(surviving):
                    renumbered = f'<TrackItem Index="{new_index}" ObjectRef="{item.group(1)}"/>'
                    block = block.replace(item.group(0), renumbered, 1)

                return block

            # Find every <TrackItems>…</TrackItems> block (one per track) and prune it.
            self._xml = re.sub(r'<TrackItems Version="\d+">.*?</TrackItems>', prune_track_items, self._xml,
                               flags=re.DOTALL)

            # Re-collect ids after the list cleanup above may have changed things.
            live_uids = set(re.findall(_OBJECT_UID_RE, self._xml))
            live_ids = set(re.findall(_OBJECT_ID_RE, self._xml))
            to_delete: list[tuple[int, int]] = []

            for block in self.toplevel_blocks():
                # These chunk types point at their media by uuid — drop the chunk if the media is gone.
                uuid_refs = re.findall(r'<(?:Media|VideoClip|AudioClip|MasterClip) ObjectURef="([^"]+)"', block.text)

                if any(ref not in live_uids for ref in uuid_refs):
                    to_delete.append((block.start, block.end))
                    continue

                # These chunk types point at their parent by number — drop if the parent is gone.
                numeric_refs = re.findall(r'<(?:SubClip|Source|Content) ObjectRef="(\d+)"', block.text)

                if any(ref not in live_ids for ref in numeric_refs):
                    to_delete.append((block.start, block.end))

            if not to_delete:
                break

            self.remove_blocks_by_positions(to_delete)

        return self

    def toplevel_blocks(self) -> list[Block]:
        """Break the project text into its top-level chunks.

        Top-level chunks are the ones indented by exactly one tab — the direct
        children of the project root. (Chunks nested deeper are left alone; we only
        ever move whole top-level chunks around.)
        """
        blocks: list[Block] = []

        # Find every line that starts with exactly one tab followed by a tag opening.
        # The second capture group (space or >) ensures we match a real tag, not a partial word.
        for match in re.finditer(r'(?m)^\t<(\w+)([ >])', self._xml):
            tag = match.group(1)
            start = match.start()

            line_end = self._xml.index('\n', start)
            first_line = self._xml[start:line_end]

            # A chunk written on one line as <Tag .../> has no separate closing tag.
            if first_line.rstrip().endswith('/>'):
                blocks.append(Block(
                    start=start,
                    end=line_end + 1,
                    tag=tag,
                    text=self._xml[start:line_end + 1],
                ))

                continue

            closing = f'\n\t</{tag}>'
            closing_pos = self._xml.find(closing, start)

            # No closing tag found — malformed or not a real block, skip silently.
            if closing_pos == -1:
                continue

            end = closing_pos + len(closing) + 1
            blocks.append(Block(start, end, tag, self._xml[start:end]))

        return blocks


_CLIP_MEDIA_TYPES = {
    "ClipProjectItem",                 # the clip's entry in the project panel
    "MasterClip",                      # container grouping the video and audio sides of one file
    "AudioClip",                       # audio half of a master clip
    "VideoClip",                       # video half of a master clip
    "SubClip",                         # a timeline slot that plays a portion of a master clip
    "Media",                           # the file reference — path, streams, codec info
    "AudioStream",                     # an audio stream within the media file
    "VideoStream",                     # a video stream within the media file
    "AudioMediaSource",                # raw audio data source for an audio stream
    "VideoMediaSource",                # raw video data source for a video stream
    "Markers",                         # in/out markers attached to a clip
    "AudioComponentChain",             # chain of audio effects on a clip
    "ClipLoggingInfo",                 # logging metadata (scene, shot, description)
    "SecondaryContent",                # supplementary clip data (waveform cache path, etc.)
    "ClipChannelSerializer",           # per-channel clip data serializer
    "ClipChannelGroupVectorSerializer",# a group of per-channel serializers
    "ClipChannelVectorSerializer",     # a list of per-channel serializers
}


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
    # Replace numbers only when they appear as ObjectID="N" or ObjectRef="N" —
    # not as bare numbers that could match something unrelated.
    for old_id, new_id in id_remap.items():
        clone = re.sub(rf'((?:ObjectID|ObjectRef)="){re.escape(old_id)}"', rf'\g<1>{new_id}"', clone)

    for old_uid, new_uid in uid_remap.items():
        clone = clone.replace(old_uid, new_uid)

    return clone
