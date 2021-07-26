from collections import Iterable
from pathlib import Path
from typing import List

from justin_utils.singleton import Singleton

from justin.actions.named.stage.logic.base import Check, Extractor
from justin.shared.models.photoset import Photoset


class Place:
    def __init__(self) -> None:
        super().__init__()

        self.incoming_checks: List[Check] = None
        self.outcoming_checks: List[Check] = None
        self.path: Path = None
        self.hooks: Iterable[Extractor] = None


class PlacesManager(Singleton):
    def place_by_command(self, command: str, photoset: Photoset) -> Place:
        pass

    def place_by_path(self, path: Path) -> Path:
        pass
