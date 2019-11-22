import json
from abc import abstractmethod
from pathlib import Path


class Metafile:
    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> 'Metafile':
        pass

    @classmethod
    def read(cls, path: Path):
        if path.exists() and path.stat().st_size > 0:
            with path.open() as metafile_file:
                json_dict = json.load(metafile_file)
        else:
            json_dict = {}

        return cls.from_dict(json_dict)

    def write(self, path: Path):
        with path.open(mode="w") as metafile_file:
            json_dict = self.to_dict()

            json.dump(json_dict, metafile_file, indent=4)
