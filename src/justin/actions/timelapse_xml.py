import gzip
import re
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

        self._xml = xml

    @classmethod
    def from_prproj(cls, path: Path) -> Self:
        with gzip.open(path, 'rb') as f:
            xml = f.read().decode('utf-8')

        return cls(xml)

    def to_prproj(self, path: Path) -> None:
        with gzip.open(path, 'wb') as f:
            f.write(self._xml.encode('utf-8'))

    def remove_blocks_by_positions(self, positions: list[tuple[int, int]]) -> Self:
        # Тупо вырезать из строки кусок между началом блока и конца блока. Другой вопрос, что тут как бы блок становится невалидным.
        # Может тут тупо сделать remove blocks и принимать список блоков, а не таплов? 

        # Cut from the end backwards, so cutting one chunk doesn't shift the
        # positions of the chunks we haven't cut yet.
        for start, end in sorted(positions, reverse=True):
            self._xml = self._xml[:start] + self._xml[end:]

        return self

    def toplevel_blocks(self) -> list[Block]:
        """Break the project text into its top-level chunks.

        Top-level chunks are the ones indented by exactly one tab — the direct
        children of the project root. (Chunks nested deeper are left alone; we only
        ever move whole top-level chunks around.)
        """
        blocks: list[Block] = []

        # ? what is this regex
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

            # ? what is it? Not closed tag and not error?
            if closing_pos == -1:
                continue

            end = closing_pos + len(closing) + 1
            blocks.append(Block(start, end, tag, self._xml[start:end]))

        return blocks
