import gzip
import re
import uuid
from pathlib import Path
from typing import Self, NamedTuple


class Block(NamedTuple):
    """One chunk of the project, and where it sits in the raw text.

    ``text`` is the chunk's full ``<Tag ...>...</Tag>`` snippet. ``start`` and
    ``end`` are where that snippet begins and ends in the whole file, so we can
    cut it out or drop it back in by slicing the string at those positions.
    """
    start: int
    end: int
    tag: str
    text: str

class Xml:
    def __init__(self, xml: str):
        super().__init__()

        self.xml = xml

    @classmethod
    def from_prproj(cls, path: Path) -> Self:
        with gzip.open(path, 'rb') as f:
            xml = f.read().decode('utf-8')

        return cls(xml)

    def to_prproj(self, path: Path) -> None:
        with gzip.open(path, 'wb') as f:
            f.write(self.xml.encode('utf-8'))

    def remove_blocks_by_positions(self, positions: list[tuple[int, int]]) -> Self:
        # Тупо вырезать из строки кусок между началом блока и конца блока. Другой вопрос, что тут как бы блок становится невалидным.
        # Может тут тупо сделать remove blocks и принимать список блоков, а не таплов? 

        # Cut from the end backwards, so cutting one chunk doesn't shift the
        # positions of the chunks we haven't cut yet.
        for start, end in sorted(positions, reverse=True):
            self.xml = self.xml[:start] + self.xml[end:]

        return self

    def toplevel_blocks(self) -> list[Block]:
        """Break the project text into its top-level chunks.

        Top-level chunks are the ones indented by exactly one tab — the direct
        children of the project root. (Chunks nested deeper are left alone; we only
        ever move whole top-level chunks around.)
        """
        blocks: list[Block] = []

        # ? what is this regex
        for match in re.finditer(r'(?m)^\t<(\w+)([ >])', self.xml):
            tag = match.group(1)
            start = match.start()

            line_end = self.xml.index('\n', start)
            first_line = self.xml[start:line_end]

            # A chunk written on one line as <Tag .../> has no separate closing tag.
            if first_line.rstrip().endswith('/>'):
                blocks.append(Block(
                    start=start,
                    end=line_end + 1,
                    tag=tag,
                    text=self.xml[start:line_end + 1],
                ))

                continue

            closing = f'\n\t</{tag}>'
            closing_pos = self.xml.find(closing, start)

            # ? what is it? Not closed tag and not error?
            if closing_pos == -1:
                continue

            end = closing_pos + len(closing) + 1
            blocks.append(Block(start, end, tag, self.xml[start:end]))

        return blocks


_CLIP_MEDIA_TYPES = {
    "ClipProjectItem", "MasterClip", "AudioClip", "VideoClip", "SubClip",
    "Media", "AudioStream", "VideoStream", "AudioMediaSource", "VideoMediaSource",
    "Markers", "AudioComponentChain", "ClipLoggingInfo",
    "SecondaryContent", "ClipChannelSerializer",
    "ClipChannelGroupVectorSerializer", "ClipChannelVectorSerializer",
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
        own_id = re.search(r'ObjectID="(\d+)"', block.text[:120])

        if own_id and block.tag in _CLIP_MEDIA_TYPES:
            media_idxs_by_id.setdefault(own_id.group(1), []).append(idx)

        own_uid = re.search(r'ObjectUID="([^"]+)"', block.text[:120])

        if own_uid:
            idx_by_uid[own_uid.group(1)] = idx

    reached = set(entry_idxs)
    frontier = list(entry_idxs)
    while frontier:
        block = blocks[frontier.pop()]
        for ref in re.finditer(r'ObjectRef="(\d+)"', block.text):
            for target in media_idxs_by_id.get(ref.group(1), []):
                if target not in reached:
                    reached.add(target)
                    frontier.append(target)
        for uref in re.finditer(r'ObjectURef="([^"]+)"', block.text):
            target = idx_by_uid.get(uref.group(1))
            if target is not None and blocks[target].tag in _CLIP_MEDIA_TYPES and target not in reached:
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

    numeric_ids = sorted(set(re.findall(r'ObjectID="(\d+)"', combined)), key=int)
    id_remap = {old: str(int(old) + id_offset) for old in numeric_ids}

    identity_uids = set(re.findall(r'Object(?:UID|URef)="([0-9a-f-]{36})"', combined))
    identity_uids |= set(re.findall(r'<ID>([0-9a-f-]{36})</ID>', combined))
    uid_remap = {old: str(uuid.uuid4()) for old in identity_uids}

    clone = combined.replace(old_name, new_name)
    for old_id, new_id in id_remap.items():
        clone = re.sub(rf'((?:ObjectID|ObjectRef)="){re.escape(old_id)}"', rf'\g<1>{new_id}"', clone)
    for old_uid, new_uid in uid_remap.items():
        clone = clone.replace(old_uid, new_uid)
    return clone


def remove_dangling_refs(xml: str) -> str:
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
        live_uids = set(re.findall(r'ObjectUID="([^"]+)"', xml))
        live_ids = set(re.findall(r'ObjectID="(\d+)"', xml))

        def prune_panel_items(items_block: re.Match) -> str:
            def keep(item: re.Match) -> str:
                uref = re.search(r'ObjectURef="([^"]+)"', item.group(0))
                if uref and uref.group(1) not in live_uids:
                    return ''
                return item.group(0)
            return re.sub(r'[^\S\n]*<Item [^/]*/>\n', keep, items_block.group(0))

        xml = re.sub(r'<Items Version="\d+">.*?</Items>', prune_panel_items, xml, flags=re.DOTALL)

        def prune_track_items(track_items_block: re.Match) -> str:
            def keep(item: re.Match) -> str:
                ref = re.search(r'ObjectRef="(\d+)"', item.group(0))
                if ref and ref.group(1) not in live_ids:
                    return ''
                return item.group(0)
            block = re.sub(r'[^\S\n]*<TrackItem [^/]*/>\n', keep, track_items_block.group(0))
            surviving = list(re.finditer(r'<TrackItem Index="\d+" ObjectRef="(\d+)"/>', block))
            for new_index, item in enumerate(surviving):
                renumbered = f'<TrackItem Index="{new_index}" ObjectRef="{item.group(1)}"/>'
                block = block.replace(item.group(0), renumbered, 1)
            return block

        xml = re.sub(r'<TrackItems Version="\d+">.*?</TrackItems>', prune_track_items, xml, flags=re.DOTALL)

        live_uids = set(re.findall(r'ObjectUID="([^"]+)"', xml))
        live_ids = set(re.findall(r'ObjectID="(\d+)"', xml))
        to_delete: list[tuple[int, int]] = []
        for block in Xml(xml).toplevel_blocks():
            uuid_refs = re.findall(r'<(?:Media|VideoClip|AudioClip|MasterClip) ObjectURef="([^"]+)"', block.text)
            if any(ref not in live_uids for ref in uuid_refs):
                to_delete.append((block.start, block.end))
                continue
            numeric_refs = re.findall(r'<(?:SubClip|Source|Content) ObjectRef="(\d+)"', block.text)
            if any(ref not in live_ids for ref in numeric_refs):
                to_delete.append((block.start, block.end))

        if not to_delete:
            break
        xml = Xml(xml).remove_blocks_by_positions(to_delete).xml

    return xml
