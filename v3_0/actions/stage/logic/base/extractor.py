from typing import List, Tuple, Any, Iterable

from v3_0.actions.stage.exceptions.no_files_for_name_error import NoFilesForNameError
from v3_0.actions.stage.logic.exceptions.extractor_error import ExtractorError
from v3_0.shared.filesystem.path_based import PathBased
from v3_0.shared.helpers import joins
from v3_0.shared.filesystem.relative_fileset import RelativeFileset
from v3_0.actions.stage.logic.base.abstract_check import AbstractCheck
from v3_0.actions.stage.logic.base.selector import Selector
from v3_0.shared.models.photoset import Photoset


class Extractor:
    def __init__(self, name: str, selector: Selector, filter_folder: str,
                 prechecks: List[AbstractCheck] = None) -> None:
        super().__init__()

        if not prechecks:
            prechecks = []

        self.__name = name
        self.__selector = selector
        self.__filter_folder = filter_folder
        self.__prechecks = prechecks

    @property
    def selector(self) -> Selector:
        return self.__selector

    def __run_prechecks(self, photoset: Photoset) -> bool:
        return all([precheck.is_good(photoset) for precheck in self.__prechecks])

    @staticmethod
    def __validate_join(join: Iterable[Tuple[str, Any]], name: str):
        names_of_unjoined_files = []

        for source_name, source in join:
            if source is None:
                names_of_unjoined_files.append(source_name)

        if names_of_unjoined_files:
            unjoined_files_names_string = ", ".join(names_of_unjoined_files)

            raise NoFilesForNameError(f"Unable to extract {name}: {unjoined_files_names_string}")

    def files_to_extract(self, photoset: Photoset) -> List[PathBased]:
        selection = self.__selector.select(photoset)

        jpegs_join = joins.left(
            selection,
            photoset.big_jpegs,
            lambda s, f: s == f.stem()
        )

        self.__validate_join(jpegs_join, "jpegs")

        sources_join = list(joins.left(
            selection,
            photoset.sources,
            lambda s, f: s == f.stem()
        ))

        self.__validate_join(sources_join, "sources")

        jpegs_to_move = [e[1] for e in jpegs_join]

        sources_contents_to_move = []

        for sources_pair in sources_join:
            for file in sources_pair[1].files():
                sources_contents_to_move.append(file)

        files_to_move = jpegs_to_move + sources_contents_to_move

        return files_to_move

    def forward(self, photoset: Photoset):
        for part in photoset.parts:
            if not self.__run_prechecks(part):
                raise ExtractorError(f"Failed prechecks while running {self.__name} extractor forward on {part.name}")

            files_to_move = self.files_to_extract(part)
            files_to_move = list(set(files_to_move))

            virtual_set = RelativeFileset(part.path, files_to_move)

            virtual_set.move_down(self.__filter_folder)

        photoset.tree.refresh()

    def backwards(self, photoset: Photoset):
        for part in photoset.parts:
            if not self.__run_prechecks(part):
                raise ExtractorError(f"Failed prechecks while running {self.__name} extractor backwards on {part.name}")

            filtered = part.tree[self.__filter_folder]

            if not filtered:
                return

            filtered_photoset = Photoset(filtered)

            if not self.__run_prechecks(filtered_photoset):
                raise ExtractorError(f"Failed prechecks while running {self.__name} extractor backwards on {part.name}/"
                                     f"{self.__filter_folder}")

            filtered_set = RelativeFileset(filtered.path, filtered.flatten())

            filtered_set.move_up()

        photoset.tree.refresh()
