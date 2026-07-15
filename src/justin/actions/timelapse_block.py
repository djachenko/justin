import re
from typing import NamedTuple

from justin.actions.timelapse_re import _OBJECT_ID_RE


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
        m = re.search(_OBJECT_ID_RE, self.header)
        return m.group(1) if m else None

    @property
    def span(self) -> tuple[int, int]:
        return self.start, self.end
