from typing import List

from filesystem import fs
from filesystem.path_interpretation import PathInterpretation


class Path(PathInterpretation):
    @staticmethod
    def __separator() -> str:
        return fs.SEPARATOR

    def __init__(self, parts: List[str]) -> None:
        super().__init__()

        non_empty_parts = [part for part in parts if part]

        self.__parts = non_empty_parts

    def append_component(self, *components: str) -> 'Path':
        components = [component for component in components if component]

        return Path.from_parts(self.__parts + components)

    def parent(self) -> 'Path':
        return Path.from_parts(self.__parts[:-1])

    def to_string(self) -> str:
        return Path.__separator().join(self.__parts)

    def exists(self) -> bool:
        return fs.path_exists__(self.to_string())

    def is_subpath(self, path: 'Path') -> bool:
        return path.to_string().startswith(self.to_string())

    @property
    def depth(self) -> int:
        return len(self.parts)

    def difference(self, path: 'Path') -> str:
        assert path.to_string().startswith(self.to_string())

        other_path = path.to_string()
        self_path = self.to_string()

        other_path = other_path.replace(self_path, "")
        other_path = other_path[1:]

        return other_path

    @property
    def parts(self):
        return self.__parts

    def __str__(self) -> str:
        return self.to_string()

    def __eq__(self, o: object) -> bool:
        if isinstance(o, str):
            return o == self.to_string()

        if isinstance(o, Path):
            return o.to_string() == self.to_string()

        return super().__eq__(o)

    @classmethod
    def from_string(cls, path: str) -> 'Path':
        path = Path.cleanse_path(path)

        result = Path.from_parts(path.split(cls.__separator()))

        return result

    @classmethod
    def from_parts(cls, parts: List[str]) -> 'Path':
        return cls(parts)

    @staticmethod
    def cleanse_path(path: str) -> str:
        while "\\" in path:
            path = path.replace("\\", "/")

        path = path.strip("/")

        return path

    def __contains__(self, item):
        return item in self.to_string()
