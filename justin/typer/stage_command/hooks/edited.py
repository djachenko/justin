from typing import List

from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.abstracts.hook import Hook
from justin.typer.stage_command.abstracts.stem_file_mover import StemFileMover


class EditedHook(StemFileMover, Hook):
    @property
    def name(self) -> str:
        return "edited hook"

    @property
    def folder(self) -> str:
        return "edited"

    def select_stems(self, photoset: Photoset) -> List[str]:
        return [result.stem for result in photoset.results]
