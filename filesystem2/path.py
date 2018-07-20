from typing import List

from filesystem import fs


class Path:
    @staticmethod
    def separator() -> str:
        return fs.SEPARATOR

    def __init__(self, parts: List[str]) -> None:
        super().__init__()

        non_empty_parts = [part for part in parts if part]

        self.__parts = non_empty_parts

    def append_component(self, *components: str) -> 'Path':
        components = [component for component in components if component]

        return self.from_parts(self.__parts + components)

    def parent(self) -> 'Path':
        return self.from_parts(self.parts[:-1])

    def to_string(self) -> str:
        return Path.separator().join(self.__parts)

    def is_subpath(self, path: 'Path') -> bool:
        return path.to_string().startswith(self.to_string())

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
    def from_string(cls, path: str):
        path = Path.cleanse_path(path)

        result = cls.from_parts(path.split(cls.separator()))

        return result

    @classmethod
    def from_parts(cls, parts: List[str]):
        return cls(parts)

    @staticmethod
    def cleanse_path(path: str) -> str:
        while "\\" in path:
            path = path.replace("\\", "/")

        path = path.strip("/")

        return path

    def __contains__(self, item):
        return item in self.to_string()
