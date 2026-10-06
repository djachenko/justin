import sys
from abc import ABC, abstractmethod
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from justin_utils import util
from justin_utils.filesystem import open_file_manager


class FixMetafileOutput(ABC):
    @abstractmethod
    def on_fixing_part(self, name: str) -> None:
        pass

    @abstractmethod
    def on_no_such_post(self) -> None:
        pass

    @abstractmethod
    def ask_post_action(self, path: Path) -> str:
        """Prompt for what to do with an unbound post folder.

        Opens the file manager on empty input and re-prompts.
        Returns a non-empty answer: "-" to skip, or a post ID string.
        """
        pass

    @abstractmethod
    def ask_timelapse_community(self, options: list[str]) -> str:
        pass

    @abstractmethod
    def ask_community_id(self) -> str:
        pass


class PlainFixMetafileOutput(FixMetafileOutput):
    def on_fixing_part(self, name: str) -> None:
        print(f"Fixing metafile for {name} photoset.")

    def on_no_such_post(self) -> None:
        print("There is no such post")

    def ask_post_action(self, path: Path) -> str:
        while True:
            answer = input(
                f"You have folder \"{path}\" without bound post. What would you like?\n"
                f"* Enter a number - bind to existing post\n"
                f"* Enter a \"-\" symbol - leave it as is\n"
                f"* Just press Enter - open folder\n"
                f"> "
            ).strip()

            if answer != "":
                return answer

            open_file_manager(path)

    def ask_timelapse_community(self, options: list[str]) -> str:
        return util.ask_for_choice("Where was timelapse published?", options)

    def ask_community_id(self) -> str:
        return input("Enter community id: ")


class RichFixMetafileOutput(FixMetafileOutput):
    def __init__(self) -> None:
        self.__console = Console()

    def on_fixing_part(self, name: str) -> None:
        self.__console.print(f"[bold]{name}[/bold]")

    def on_no_such_post(self) -> None:
        self.__console.print("[red]There is no such post[/red]")

    def ask_post_action(self, path: Path) -> str:
        while True:
            self.__console.print(Panel(
                f"[yellow]{path}[/yellow] has no bound post\n\n"
                f"  [cyan]<number>[/cyan]  bind to existing post\n"
                f"  [cyan]-[/cyan]         leave as is\n"
                f"  [cyan]Enter[/cyan]     open folder",
                expand=False,
            ))

            answer = Prompt.ask(">", default="").strip()

            if answer != "":
                return answer

            open_file_manager(path)

    def ask_timelapse_community(self, options: list[str]) -> str:
        self.__console.print("[bold]Where was timelapse published?[/bold]")

        for i, option in enumerate(options, 1):
            self.__console.print(f"  [cyan]{i}[/cyan]. {option}")

        while True:
            answer = Prompt.ask(">").strip()

            if answer.isdecimal():
                idx = int(answer) - 1

                if 0 <= idx < len(options):
                    return options[idx]

            self.__console.print("[red]Invalid choice[/red]")

    def ask_community_id(self) -> str:
        return Prompt.ask("Community ID")


def make_fix_metafile_output() -> FixMetafileOutput:
    if sys.stdout.isatty():
        return RichFixMetafileOutput()

    return PlainFixMetafileOutput()


# region Demo

def _simulate(output: FixMetafileOutput) -> None:
    parts = [
        "26.03.21.hindemith_rep/26.03.21.hindemith_rep",
        "26.04.05.morningtisse/part.2",
    ]

    for part in parts:
        output.on_fixing_part(part)

    output.on_no_such_post()

    output.ask_timelapse_community(["justin", "kot_i_kit", "Other community", "Wasn't published"])
    output.ask_post_action(Path("justin/sketches/1"))


app = __import__("typer").Typer(add_completion=False)


@app.command()
def demo(renderer: str = __import__("typer").Argument("both", help="plain | rich | both")) -> None:
    import typer

    if renderer in ("plain", "both"):
        typer.echo(typer.style("\n=== plain ===\n", bold=True))
        _simulate(PlainFixMetafileOutput())

    if renderer in ("rich", "both"):
        typer.echo(typer.style("\n=== rich ===\n", bold=True))
        _simulate(RichFixMetafileOutput())


if __name__ == "__main__":
    app()

# endregion
