from abc import ABC, abstractmethod
from typing import List

import typer

from justin.typer.stage_command.problems.problem import Problem
from justin.shared.models.photoset import Photoset


# region Protocol

class ChecksReporter(ABC):
    @abstractmethod
    def on_photoset_start(self, photoset: Photoset, from_stage: str, to_stage: str) -> None:
        pass

    @abstractmethod
    def on_check_passed(self, name: str) -> None:
        pass

    @abstractmethod
    def on_check_failed(self, name: str, problems: List[Problem]) -> None:
        pass

    @abstractmethod
    def ask_fix(self, message: str) -> bool:
        pass

    @abstractmethod
    def on_fix_failed(self, problems: List[Problem]) -> None:
        pass

    @abstractmethod
    def on_photoset_success(self, photoset: Photoset, to_stage: str) -> None:
        pass

    @abstractmethod
    def on_photoset_failure(self, photoset: Photoset, problems: List[Problem]) -> None:
        pass


# endregion


# region Typer implementation

class TyperChecksReporter(ChecksReporter):
    _PASS = typer.style("✓", fg=typer.colors.GREEN, bold=True)
    _FAIL = typer.style("✗", fg=typer.colors.RED, bold=True)
    _ARROW = typer.style("→", fg=typer.colors.BRIGHT_BLACK)

    def on_photoset_start(self, photoset: Photoset, from_stage: str, to_stage: str) -> None:
        header = (
            f"\n{typer.style(photoset.name, bold=True)}"
            f"  {self._ARROW}  "
            f"{typer.style(to_stage, fg=typer.colors.CYAN)}"
        )
        typer.echo(header)
        typer.echo(typer.style("─" * 50, fg=typer.colors.BRIGHT_BLACK))

    def on_check_passed(self, name: str) -> None:
        typer.echo(f"  {self._PASS}  {name}")

    def on_check_failed(self, name: str, problems: List[Problem]) -> None:
        typer.echo(f"  {self._FAIL}  {typer.style(name, fg=typer.colors.RED)}")

        for problem in problems:
            typer.echo(f"     {typer.style(str(problem), fg=typer.colors.YELLOW)}")

    def ask_fix(self, message: str) -> bool:
        return typer.confirm(f"     {message}", default=False)

    def on_fix_failed(self, problems: List[Problem]) -> None:
        typer.secho("\n  Fix failed:", fg=typer.colors.RED, bold=True)

        for problem in problems:
            typer.echo(f"     {problem}")

    def on_photoset_success(self, photoset: Photoset, to_stage: str) -> None:
        typer.echo(typer.style("─" * 50, fg=typer.colors.BRIGHT_BLACK))
        typer.secho(f"  Moved to {to_stage} successfully\n", fg=typer.colors.GREEN)

    def on_photoset_failure(self, photoset: Photoset, problems: List[Problem]) -> None:
        typer.echo(typer.style("─" * 50, fg=typer.colors.BRIGHT_BLACK))
        typer.secho(f"  Unable to move {photoset.name}\n", fg=typer.colors.RED, bold=True)


# endregion
