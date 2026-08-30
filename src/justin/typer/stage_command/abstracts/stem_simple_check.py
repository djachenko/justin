from abc import ABC

from justin.typer.stage_command.abstracts.simple_check import SimpleCheck
from justin.typer.stage_command.abstracts.stem_checking import StemChecking


class StemSimpleCheck(StemChecking, SimpleCheck, ABC):
    pass
