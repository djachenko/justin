from abc import ABC

from justin_utils.filesystem import PathBased

from justin.shared.helpers import photoset_utils
from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.abstracts.file_mover import FileMover
from justin.typer.stage_command.abstracts.stem_selecting import StemSelecting


class StemFileMover(FileMover, StemSelecting, ABC):
    def files_to_extract(self, photoset: Photoset) -> list[PathBased]:
        return photoset_utils.files_by_stems(self.select_stems(photoset), photoset)
