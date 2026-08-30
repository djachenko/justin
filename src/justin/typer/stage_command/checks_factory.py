

from functools import cached_property
from typing import List

from justin.shared.structure import Structure
from justin.typer.stage_command.abstracts.check import Check
from justin.typer.stage_command.checks.simple.everything_published import EverythingIsPublishedCheck
from justin.typer.stage_command.checks.simple.gif_sources import GifSourcesCheck
from justin.typer.stage_command.checks.simple.metadata import MetadataCheck
from justin.typer.stage_command.checks.simple.metafile_state import MetafilesExistCheck, MetafilesPublishedCheck
from justin.typer.stage_command.checks.extracting.odd_selection import OddSelectionCheck
from justin.typer.stage_command.checks.simple.progress import ProgressResultsCheck
from justin.typer.stage_command.checks.extracting.structure import StructureCheck
from justin.typer.stage_command.checks.extracting.unselected import UnselectedCheck


class ChecksFactory:
    def __init__(self, photoset_structure: Structure) -> None:
        self.__photoset_structure = photoset_structure

    # region Prechecks-free

    @cached_property
    def metadata(self) -> Check:
        return MetadataCheck()

    @cached_property
    def gif_sources(self) -> Check:
        return GifSourcesCheck()

    @cached_property
    def everything_is_published(self) -> Check:
        return EverythingIsPublishedCheck()

    @cached_property
    def progress_results(self) -> Check:
        return ProgressResultsCheck()

    @cached_property
    def metafiles_exist(self) -> Check:
        return MetafilesExistCheck()

    @cached_property
    def metafiles_published(self) -> Check:
        return MetafilesPublishedCheck()

    # endregion

    # region With prechecks

    @cached_property
    def unselected(self) -> Check:
        return UnselectedCheck(prechecks=self.__metadata_prechecks)

    @cached_property
    def odd_selection(self) -> Check:
        return OddSelectionCheck(prechecks=self.__metadata_prechecks)

    @cached_property
    def structure(self) -> Check:
        return StructureCheck(
            structure=self.__photoset_structure,
            prechecks=self.__metadata_prechecks,
        )

    # endregion

    # region Private

    @cached_property
    def __metadata_prechecks(self) -> List[Check]:
        return [self.metadata]

    # endregion