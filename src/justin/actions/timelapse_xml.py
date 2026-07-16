import gzip
import re
from pathlib import Path
from typing import Self

from justin.actions.timelapse_block import Block, Blocks
from justin.actions.timelapse_re import TimelapseRe
from justin.actions.timelapse_tags import Tag


class Xml:
    def __init__(self, xml: str):
        super().__init__()

        self._xml = xml

    @property
    def text(self) -> str:
        return self._xml

    @classmethod
    def from_prproj(cls, path: Path) -> Self:
        with gzip.open(path, 'rb') as f:
            xml = f.read().decode('utf-8')

        return cls(xml)

    @classmethod
    def from_gzip_bytes(cls, data: bytes) -> Self:
        return cls(gzip.decompress(data).decode('utf-8'))

    def to_prproj(self, path: Path) -> None:
        with gzip.open(path, 'wb') as f:
            f.write(self._xml.encode('utf-8'))

    def max_object_id(self) -> int:
        """The highest numeric ObjectID in the project — used to pick a safe id_offset when cloning."""
        return max(int(i) for i in re.findall(TimelapseRe.OBJECT_ID, self._xml))

    def find_panel_item_index(self, uid: str) -> int | None:
        """Index of the <Item ObjectURef="uid"/> entry in the project panel's clip list, or None."""
        if m := re.search(TimelapseRe.panel_item(uid), self._xml):
            return int(m.group(1))

        return None

    def replace(self, old: str, new: str) -> None:
        self._xml = self._xml.replace(old, new)

    def replace_range(self, start: int, end: int, text: str) -> None:
        self._xml = self._xml[:start] + text + self._xml[end:]

    def replace_ranges(self, edits: list[tuple[int, int, str]]) -> Self:
        """Apply several (start, end, replacement) edits in one pass.

        The ranges must not overlap. Edits are applied from the end of the string
        backwards, so each one's offsets stay valid however the later (earlier in
        the string) replacements change length.
        """
        for start, end, text in sorted(edits, reverse=True):
            self.replace_range(start, end, text)

        return self

    def insert(self, position: int, text: str) -> None:
        self.replace_range(position, position, text)

    def sub(self, pattern: str, repl, count: int = 0, flags: int = 0) -> None:
        self._xml = re.sub(pattern, repl, self._xml, count=count, flags=flags)

    def remove_blocks_by_positions(self, positions: list[tuple[int, int]]) -> Self:
        # Removing a block is just replacing its range with nothing.
        return self.replace_ranges([(start, end, "") for start, end in positions])

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
            live_uids = set(re.findall(TimelapseRe.OBJECT_UID, self._xml))
            live_ids = set(re.findall(TimelapseRe.OBJECT_ID, self._xml))

            def prune_panel_items(items_block: re.Match) -> str:
                def keep(item: re.Match) -> str:
                    # Each <Item .../> line points at a clip by uuid. Drop the line if that clip is gone.
                    uref = re.search(TimelapseRe.OBJECT_UREF, item.group(0))

                    if uref and uref.group(1) not in live_uids:
                        return ''

                    return item.group(0)

                # Match any self-closing <Item .../> line (with optional leading spaces).
                # The space after "<Item " is intentional — without it the pattern would also
                # match "<Items " and eat the list's own opening tag.
                return re.sub(TimelapseRe.ANY_PANEL_ITEM_LINE, keep, items_block.group(0))

            # Find every <Items>…</Items> block (the project panel's clip list) and prune it.
            self._xml = re.sub(TimelapseRe.PANEL_ITEMS_BLOCK, prune_panel_items, self._xml, flags=re.DOTALL)

            def prune_track_items(track_items_block: re.Match) -> str:
                def keep(item: re.Match) -> str:
                    # Each <TrackItem .../> line points at a clip by number. Drop if that clip is gone.
                    ref = re.search(TimelapseRe.OBJECT_REF, item.group(0))
                    if ref and ref.group(1) not in live_ids:
                        return ''
                    return item.group(0)

                # Same trap: "<TrackItem " needs the space so it doesn't match "<TrackItems ".
                block = re.sub(TimelapseRe.ANY_TRACK_ITEM_LINE, keep, track_items_block.group(0))
                # After dropping entries the Index attributes have gaps; renumber them 0, 1, 2, …
                surviving = list(re.finditer(TimelapseRe.TRACK_ITEM_OBJECTREF, block))

                for new_index, item in enumerate(surviving):
                    renumbered = f'<TrackItem Index="{new_index}" ObjectRef="{item.group(1)}"/>'
                    block = block.replace(item.group(0), renumbered, 1)

                return block

            # Find every <TrackItems>…</TrackItems> block (one per track) and prune it.
            self._xml = re.sub(TimelapseRe.ANY_TRACK_ITEMS_BLOCK, prune_track_items, self._xml, flags=re.DOTALL)

            # Re-collect ids after the list cleanup above may have changed things.
            live_uids = set(re.findall(TimelapseRe.OBJECT_UID, self._xml))
            live_ids = set(re.findall(TimelapseRe.OBJECT_ID, self._xml))
            to_delete: list[tuple[int, int]] = []

            for block in self.toplevel_blocks():
                # These chunk types point at their media by uuid — drop the chunk if the media is gone.
                uuid_refs = re.findall(TimelapseRe.UUID_REF_TAGS, block.text)

                if any(ref not in live_uids for ref in uuid_refs):
                    to_delete.append(block.span)
                    continue

                # These chunk types point at their parent by number — drop if the parent is gone.
                numeric_refs = re.findall(TimelapseRe.NUMERIC_REF_TAGS, block.text)

                if any(ref not in live_ids for ref in numeric_refs):
                    to_delete.append(block.span)

            if not to_delete:
                break

            self.remove_blocks_by_positions(to_delete)

        return self

    def toplevel_blocks(self) -> Blocks:
        """Break the project text into its top-level chunks.

        Top-level chunks are the ones indented by exactly one tab — the direct
        children of the project root. (Chunks nested deeper are left alone; we only
        ever move whole top-level chunks around.)
        """
        blocks: Blocks = Blocks()

        # Find every line that starts with exactly one tab followed by a tag opening.
        # The second capture group (space or >) ensures we match a real tag, not a partial word.
        for match in re.finditer(TimelapseRe.TOPLEVEL_BLOCK_START, self._xml):
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
    Tag.ClipProjectItem,
    Tag.MasterClip,
    Tag.AudioClip,
    Tag.VideoClip,
    Tag.SubClip,
    Tag.Media,
    Tag.AudioStream,
    Tag.VideoStream,
    Tag.AudioMediaSource,
    Tag.VideoMediaSource,
    Tag.Markers,
    Tag.AudioComponentChain,
    Tag.ClipLoggingInfo,
    Tag.SecondaryContent,
    Tag.ClipChannelSerializer,
    Tag.ClipChannelGroupVectorSerializer,
    Tag.ClipChannelVectorSerializer,
}
