from abc import ABC

from justin.typer.stage_command.abstracts.stem_checking import StemChecking  # noqa: F401
from justin.typer.stage_command.abstracts.stem_file_mover import StemFileMover
from justin.typer.stage_command.abstracts.extracting_check import ExtractingCheck


class StemExtractingCheck(StemChecking, ExtractingCheck, StemFileMover, ABC):
    pass
