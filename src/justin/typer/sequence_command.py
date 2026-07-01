from pathlib import Path
from typing import Annotated, List, Iterable

import typer
from typer import Typer, Argument

from justin.typer.base_commands.pattern_command import Extra
from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin.shared.models.exif import exif_sorted
from justin.typer.base_commands.pattern_command import PatternCommand


class SequenceCommand(PatternCommand):
    def __init__(
        self,
        context: Context,
        patterns: Iterable[Path],
        prefix: str | None,
        start: int
    ):
        super().__init__(context, patterns)

        self.__prefix = prefix
        self.__start = start
    
    def run_for_folder(self, folder: Folder, extra: Extra) -> None:
        files = exif_sorted(folder.files)
        files = [file.path for file in files]

        for index, file in enumerate(files, start=self.__start):
            new_stem = f"{index:04}"

            if self.__prefix:
                new_stem = f"{self.__prefix}_{new_stem}"

            new_path = file.with_stem(new_stem)
            file.rename(new_path)


app = Typer()


@app.command()
def sequence(
    context: Annotated[typer.Context, Argument()],
    pattern: Annotated[List[Path], Argument()] = (Path.cwd(),),
    prefix: Annotated[str | None, typer.Argument()] = None,
    start: Annotated[int, typer.Argument()] = 0
) -> None:
    SequenceCommand(context.obj, pattern, prefix, start).run()


