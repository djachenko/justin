import re
from typing import Iterable, NamedTuple

from justin.actions.timelapse_re import TimelapseRe


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

    # ObjectID / ObjectUID always sit in the opening tag — the very first line.
    # ~110 chars; 120 comfortably covers the longest opening tags we've seen.
    # Example: \t<MasterClip ObjectID="42" ObjectUID="a1b2c3d4-…" ClassID="be4a3c7e-…">
    _HEADER_LEN = 120

    @property
    def header(self) -> str:
        return self.text[:self._HEADER_LEN]

    @property
    def id(self) -> str | None:
        if m := re.search(TimelapseRe.OBJECT_ID, self.header):
            return m.group(1)
        else:
            return None

    @property
    def span(self) -> tuple[int, int]:
        return self.start, self.end


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
        return Blocks(block for block in self if block.tag == tag)

    def containing(self, marker: str) -> "Blocks":
        return Blocks(block for block in self if marker in block.text)

    def by_id(self, tag: str, block_id: str | None) -> Block | None:
        if block_id is None:
            return None

        return next((block for block in self if block.tag == tag and block.id == block_id), None)

    def first(self) -> Block | None:
        if self:
            return self[0]
        else:
            return None

    def __str__(self) -> str:
        """The raw text of these blocks, concatenated in order — a section ready to
        splice into a document (or hand to a Sound to realize)."""
        return "".join(block.text for block in self)

    def reachable_cluster(self, seeds: Iterable[Block], member_tags: set[str]) -> "Blocks":
        """Every block reachable from ``seeds`` by following id/uuid pointers.

        A clip isn't one block — it's a cluster wired together by pointers, and
        only a few blocks in it name the file; the rest are reached by walking
        references. ``member_tags`` says which tags count as cluster members: a
        numeric pointer's tag doesn't reveal its target's kind (``<Clip
        ObjectRef="56"/>`` may be a Video- or AudioClip), so we accept any
        member-tag block carrying that id; uuid pointers are unambiguous.

        Returns the cluster as a ``Blocks``, ordered by position in the document.
        """
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
        frontier = list(reached.values())

        while frontier:
            block = frontier.pop()

            for ref in re.finditer(TimelapseRe.OBJECT_REF, block.text):
                for target in members_by_id.get(ref.group(1), []):
                    if target.start not in reached:
                        reached[target.start] = target
                        frontier.append(target)

            for uref in re.finditer(TimelapseRe.OBJECT_UREF, block.text):
                target = block_by_uid.get(uref.group(1))

                if target is None or target.tag not in member_tags or target.start in reached:
                    continue

                reached[target.start] = target
                frontier.append(target)

        return Blocks(sorted(reached.values(), key=lambda block: block.start))
