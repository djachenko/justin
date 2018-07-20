from typing import List

from filesystem import fs
from filesystem2.path import Path
from filesystem2.relative_path import RelativePath


class AbsolutePath(Path):
    def exists(self) -> bool:
        return fs.path_exists__(self.to_string())

    def is_subpath(self, path: 'Path') -> bool:
        return path.to_string().startswith(self.to_string())

    @property
    def depth(self) -> int:
        return len(self.parts)

    def __add__(self, other: RelativePath) -> 'AbsolutePath':
        return AbsolutePath.from_parts(self.parts + other.parts)

    def __sub__(self, other: Path) -> Path:
        if isinstance(other, AbsolutePath):
            assert other.is_subpath(self)

            result_parts = self.parts[len(other.parts):]

            return RelativePath.from_parts(result_parts)
        elif isinstance(other, RelativePath):
            assert other.end_of(self)

            result_parts = self.parts[:-len(other.parts)]

            return AbsolutePath.from_parts(result_parts)

        assert False
