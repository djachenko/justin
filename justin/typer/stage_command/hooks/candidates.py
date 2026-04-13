from typing import List

from justin_utils.util import flat_map

from justin.shared.filesystem import PathBased
from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.abstracts.file_mover import FileMover
from justin.typer.stage_command.abstracts.hook import Hook


class CandidatesHook(FileMover, Hook):
    @property
    def name(self) -> str:
        return "candidates hook"

    @property
    def folder(self) -> str:
        return "candidates"

    def files_to_extract(self, photoset: Photoset) -> List[PathBased]:
        return flat_map(source.files() for source in photoset.sources)
