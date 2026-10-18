import gzip
import re
from pathlib import Path
from typing import Self

from justin.actions.timelapse_block import Block, Blocks, Edit
from justin.actions.timelapse_re import TimelapseRe
from justin.actions.timelapse_tags import Tag


class Xml:
    """A ``.prproj``'s XML as mutable text — every edit is a text edit on it.

    Blocks and model objects taken from it are snapshots, valid until the next edit.
    """

    def __init__(self, xml: str):
        super().__init__()

        self._xml = xml

    @property
    def text(self) -> str:
        """The current project text, with every edit made so far applied."""
        return self._xml

    @classmethod
    def from_gzip_bytes(cls, data: bytes) -> Self:
        """Read a ``.prproj`` file's bytes: a ``.prproj`` is gzipped UTF-8 XML.

        :param data: the file's raw bytes.
        :returns: the project's XML.
        """
        return cls(gzip.decompress(data).decode('utf-8'))

    def to_prproj(self, path: Path) -> None:
        """Write the project to ``path`` as a ``.prproj`` — gzipped UTF-8, like Premiere saves it.

        :param path: where to write; an existing file is overwritten.
        """
        with gzip.open(path, 'wb') as f:
            f.write(self._xml.encode('utf-8'))

    def max_object_id(self) -> int:
        """The highest numeric ObjectID in the project — used to pick a safe id_offset when cloning.

        :returns: the largest ``ObjectID``.
        """
        return max(int(i) for i in re.findall(TimelapseRe.OBJECT_ID, self._xml))

    def find_panel_item_index(self, uid: str) -> int | None:
        """Index of the <Item ObjectURef="uid"/> entry in the project panel's clip list, or None.

        :param uid: the clip's ``ObjectUID``.
        :returns: the entry's ``Index``, or ``None`` if the panel does not list the clip.
        """
        if m := re.search(TimelapseRe.panel_item(uid), self._xml):
            return int(m.group(1))
        else:
            return None

    def replace(self, old: str, new: str) -> None:
        """Replace every occurrence of ``old`` with ``new`` across the whole project.

        Global on purpose — used for placeholders and template values that must
        change everywhere they appear. Not for editing one block: use an ``Edit``.

        :param old: the text to find.
        :param new: the text to put in its place.
        """
        self._xml = self._xml.replace(old, new)

    def replace_range(self, start: int, end: int, text: str) -> None:
        """Replace the text between offsets ``start`` and ``end`` with ``text``.

        Shifts every offset after ``end``, so any ``Blocks`` snapshot taken before
        is stale afterwards.

        :param start: offset where the replaced text begins.
        :param end: offset where it ends, exclusive.
        :param text: the replacement.
        """
        self._xml = self._xml[:start] + text + self._xml[end:]

    def replace_ranges(self, edits: list[Edit]) -> Self:
        """Apply several (start, end, replacement) edits in one pass.

        The ranges must not overlap. Edits are applied from the end of the string
        backwards, so each one's offsets stay valid however the later (earlier in
        the string) replacements change length.

        :param edits: non-overlapping edits, in any order.
        :returns: this ``Xml``, for chaining.
        """
        for start, end, text in sorted(edits, reverse=True):
            self.replace_range(start, end, text)

        return self

    def insert(self, position: int, text: str) -> None:
        """Insert ``text`` at offset ``position``; offsets after it shift like in ``replace_range``.

        :param position: the offset to insert at.
        :param text: the text to insert.
        """
        self.replace_range(position, position, text)

    def regex_replace(self, pattern: str, repl, count: int = 0, flags: int = 0) -> None:
        """``re.sub`` over the whole project, in place — same ``repl``, ``count`` and ``flags``.

        :param pattern: the regex to replace.
        :param repl: a replacement string or a function of the match, as in ``re.sub``.
        :param count: the most replacements to make; ``0`` replaces all.
        :param flags: ``re`` flags for ``pattern``.
        """
        self._xml = re.sub(pattern, repl, self._xml, count=count, flags=flags)

    def remove_blocks_by_positions(self, positions: list[tuple[int, int]]) -> Self:
        """Cut out the blocks at the given ``(start, end)`` spans.

        Removing a block is just replacing its range with nothing, so this goes
        through ``replace_ranges`` and the spans may come in any order. Nothing
        else is touched: pointers to the removed blocks are left dangling for
        ``remove_dangling_refs`` to clean up.

        :param positions: the blocks' spans, in any order.
        :returns: this ``Xml``, for chaining.
        """
        return self.replace_ranges([Edit(start, end, "") for start, end in positions])

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

        :returns: this ``Xml``, for chaining.
        """
        while True:
            # Collect all ids/uuids that actually exist right now.
            live_uids = set(re.findall(TimelapseRe.OBJECT_UID, self._xml))
            live_ids = set(re.findall(TimelapseRe.OBJECT_ID, self._xml))

            def prune_panel_items(items_block: re.Match) -> str:
                """The matched ``<Items>`` list without entries for clips that no longer exist.

                :param items_block: the match of an ``<Items>`` list.
                :returns: the list's text without the stale entries.
                """
                def keep(item: re.Match) -> str:
                    """The ``<Item .../>`` line itself, or ``''`` if the clip it points at by uuid is gone.

                    :param item: the match of one ``<Item .../>`` line.
                    :returns: the line, or ``''`` to drop it.
                    """
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
                """The matched ``<TrackItems>`` list without entries for gone slots, renumbered from 0.

                :param track_items_block: the match of a ``<TrackItems>`` list.
                :returns: the list's text without the stale entries, renumbered.
                """
                def keep(item: re.Match) -> str:
                    """The ``<TrackItem .../>`` line itself, or ``''`` if the slot it points at by number is gone.

                    :param item: the match of one ``<TrackItem .../>`` line.
                    :returns: the line, or ``''`` to drop it.
                    """
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

    def remove_unreachable(self) -> Self:
        """
        Remove every top-level chunk the project can no longer reach.

        Premiere saves a graph with one root — the ``Project`` chunk, the only one
        without an id — and every other chunk reachable from it by pointers.
        remove_dangling_refs only drops chunks whose own pointer broke; a chunk
        nothing points at any more (a removed cover's Markers, the SubClip of a
        sound that stays in the panel only) has no broken pointer and survives it.
        This walks pointers from the root and removes whatever it doesn't reach.

        Every tag counts as a target of a numeric pointer: a number shared by two
        classes keeps both chunks alive, which errs on the side of keeping.

        :returns: this ``Xml``, for chaining.
        """
        blocks = self.toplevel_blocks()
        reached = blocks.reachable_cluster(blocks.by_tag(Tag.Project), {block.tag for block in blocks})
        reached_starts = {block.start for block in reached}

        return self.remove_blocks_by_positions([block.span for block in blocks if block.start not in reached_starts])

    def toplevel_blocks(self) -> Blocks:
        """Break the project text into its top-level chunks.

        Top-level chunks are the ones indented by exactly one tab — the direct
        children of the project root. (Chunks nested deeper are left alone; we only
        ever move whole top-level chunks around.)

        :returns: a snapshot of the top-level blocks, in document order.
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
