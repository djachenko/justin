from abc import ABC, abstractmethod
from typing import Iterable, List, TYPE_CHECKING

from justin_utils.filesystem import File, RelativeFileset

from justin.shared.filesystem import PathBased
from justin.shared.metafiles.metafile import RootMetafile
from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.checks.base import StageCheckError

if TYPE_CHECKING:
    from justin.typer.stage_command.abstracts.check import Check


class FileMover(ABC):
    """
    Миксин — реализует fix/unfix через перемещение файлов в папку-карантин.
    prechecks прогоняются перед любым перемещением — гарантия целостности операции.
    Используется и хуками, и чеками с извлечением.
    """

    def __init__(self, prechecks: List['Check'] = None) -> None:
        self.__prechecks = prechecks or []

    @property
    @abstractmethod
    def folder(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def files_to_extract(self, photoset: Photoset) -> Iterable[PathBased]:
        raise NotImplementedError

    def fix(self, photoset: Photoset) -> None:
        self.__run_prechecks(photoset)

        files = list(self.files_to_extract(photoset))

        if not files:
            return

        RelativeFileset(photoset.path, files).move_down(self.folder)

        photoset.folder.refresh()

    def unfix(self, photoset: Photoset) -> None:
        filtered = photoset.folder[self.folder]

        if not filtered:
            return

        self.__run_prechecks(photoset)

        metafiles = [
            File(path)
            for path in RootMetafile.collect_metafile_paths(filtered)
            if path.exists()
        ]

        RelativeFileset(filtered.path, filtered.flatten() + metafiles).move_up()

        photoset.folder.refresh()

    def __run_prechecks(self, photoset: Photoset) -> None:
        for precheck in self.__prechecks:
            problems = precheck.get_problems(photoset)

            if problems:
                raise StageCheckError(problems)
