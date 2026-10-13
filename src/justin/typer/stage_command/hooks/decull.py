import json

from justin_utils.filesystem import PathBased
from typing import Iterable

from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.abstracts.file_mover import FileMover
from justin.typer.stage_command.abstracts.hook import Hook


class DecullHook(FileMover, Hook):
    @property
    def folder(self) -> str:
        return "good"
    
    def files_to_extract(self, photoset: Photoset) -> Iterable[PathBased]:
        pass
        
        
        
def check_cullen(photoset: Photoset) -> bool:
    cullen_candidates = photoset.cullen

    if not cullen_candidates:
        return True # ask if intended



    culled_path = photoset.path / "culled.json"
    if not culled_path.exists():
        # as
        return False # candidates present, no result

    with culled_path.open() as f:
        culled = json.load(f) # move to cullen as lib

    good_folder = photoset.folder / "good"

    if good_folder.exists():
        for file in good_folder.files:
            file.move_up()

        good_folder.remove()
    else:
        return False

    bad_folder = photoset.folder / "bad"

    if bad_folder.exists():
        if not bad_folder.empty():
            return False

        bad_folder.remove()

    return True