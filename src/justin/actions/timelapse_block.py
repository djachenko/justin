import re
from collections.abc import Iterable, Set
from typing import NamedTuple

from justin.actions.timelapse_re import TimelapseRe, search_group

# ObjectID / ObjectUID always sit in the opening tag — the very first line.
# ~110 chars; 120 comfortably covers the longest opening tags we've seen.
# Example: \t<MasterClip ObjectID="42" ObjectUID="a1b2c3d4-…" ClassID="be4a3c7e-…">
_HEADER_LEN = 120


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

    @property
    def header(self) -> str:
        """The start of the block's text, long enough to hold its opening tag.

        Own ids are read from here, not from the whole text: a block's body is full
        of pointers to other blocks (``ObjectRef``, ``ObjectURef``), and a search
        over the full text could pick one of those up instead of the block's own id.
        """
        return self.text[:_HEADER_LEN]

    @property
    def id(self) -> str | None:
        """The block's own ``ObjectID``, or ``None`` for uuid-identified blocks.

        Unique only among blocks of the same class — see ``timelapse_model``.
        """
        return search_group(TimelapseRe.OBJECT_ID, self.header)

    @property
    def span(self) -> tuple[int, int]:
        """``(start, end)`` — the form the ``Xml`` removal methods take."""
        return self.start, self.end


class Edit(NamedTuple):
    """A block's span, and the text that should take its place.

    Nothing is rewritten in place: an edit is *worked out* from a snapshot and only
    ``Xml`` ever applies it. That keeps the "apply from the end of the document
    backwards" discipline possible — every edit's offsets are still the snapshot's.
    """

    start: int
    end: int
    text: str


class Blocks(list[Block]):
    """A snapshot of the document's top-level blocks, with structural lookups.

    Just a ``list[Block]`` with query helpers, so it stays iterable/indexable
    everywhere a plain list is expected. Purely structural: it knows about tags,
    ids and pointers — nothing about what any given Premiere tag *means*.

    A snapshot is valid only until the next mutation of the ``Xml`` it came from:
    every edit shifts byte offsets, so re-take it (``xml.toplevel_blocks()``)
    after mutating.
    """

    def by_tag(self, tag: str) -> "Blocks":
        """The blocks whose top-level tag is ``tag``, in document order.

        Matches the tag only, not the class: one tag can name several Premiere
        classes (see ``timelapse_model``), so this is a coarse structural filter.
        """
        return Blocks(block for block in self if block.tag == tag)

    def containing(self, marker: str) -> "Blocks":
        """The blocks whose text contains ``marker`` anywhere, in document order.

        Used with the template's placeholder strings: only the blocks that name a
        file (media, panel items) carry them, so this finds a cluster's entry points.
        """
        return Blocks(block for block in self if marker in block.text)

    def first(self) -> Block | None:
        """The first block, or ``None`` if there are none."""
        return next(iter(self), None)

    def __str__(self) -> str:
        """The raw text of these blocks, concatenated in order — a section ready to
        splice into a document (or hand to ``Sound.adapt``)."""
        return "".join(block.text for block in self)

    def reachable_cluster(self, seeds: Iterable[Block], member_tags: Set[str]) -> "Blocks":
        """Every block reachable from ``seeds`` by following id/uuid pointers.

        A clip isn't one block — it's a cluster wired together by pointers, and
        only a few blocks in it name the file; the rest are reached by walking
        references. ``member_tags`` says which tags count as cluster members: a
        numeric pointer's tag doesn't reveal its target's kind (``<Clip
        ObjectRef="56"/>`` may be a Video- or AudioClip), so we accept any
        member-tag block carrying that id; uuid pointers are unambiguous.

        Returns the cluster as a ``Blocks``, ordered by position in the document.
        """
        # member_tags bounds what can be pulled in. A number names a block only
        # together with its class, and callers delete this cluster, so collecting
        # one block too many means deleting an unrelated block.
        members_by_id: dict[str, list[Block]] = {}
        block_by_uid: dict[str, Block] = {}

        for block in self:
            own_id = re.search(TimelapseRe.OBJECT_ID, block.header)

            if own_id and block.tag in member_tags:
                members_by_id.setdefault(own_id.group(1), []).append(block)

            own_uid = re.search(TimelapseRe.OBJECT_UID, block.header)

            if own_uid:
                block_by_uid[own_uid.group(1)] = block

        reached: dict[int, Block] = {block.start: block for block in seeds}
        # Not list(seeds): seeds is an Iterable and the line above already drained it.
        frontier = list(reached.values())

        while frontier:
            block = frontier.pop()

            # Numeric pointers: the number alone is ambiguous, so every member-tag
            # block carrying it counts as a target.
            for ref in re.finditer(TimelapseRe.OBJECT_REF, block.text):
                for target in members_by_id.get(ref.group(1), []):
                    if target.start not in reached:
                        reached[target.start] = target
                        frontier.append(target)

            # Uuid pointers: globally unique, so at most one target — but it still
            # has to be a member tag to join the cluster.
            for uref in re.finditer(TimelapseRe.OBJECT_UREF, block.text):
                uid_target = block_by_uid.get(uref.group(1))

                if uid_target is None or uid_target.tag not in member_tags or uid_target.start in reached:
                    continue

                reached[uid_target.start] = uid_target
                frontier.append(uid_target)

        return Blocks(sorted(reached.values(), key=lambda block: block.start))
