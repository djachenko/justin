from pathlib import Path
from typing import Iterable, Annotated, List

import typer
from typer import Argument, Typer

from justin.shared.context import Context
from justin.shared.models.photoset import Photoset
from justin.typer.base_commands.pattern_command import PatternCommand, Extra
from justin.typer.stage_command.checks.base import StageCheckError
from justin.typer.stage_command.checks_reporter import ChecksReporter, TyperChecksReporter
from justin.typer.stage_command.stages_factory import StagesFactory


class StageCommand(PatternCommand):
    __CURRENT_STAGE = "current_stage"
    __NEW_STAGE = "new_stage"

    def __init__(
        self,
        context: Context,
        patterns: Iterable[Path],
        command_name: str,
        stages_factory: StagesFactory,
        reporter: ChecksReporter,
    ) -> None:
        super().__init__(context, patterns)

        self.__command_name = command_name
        self.__stages_factory = stages_factory
        self.__reporter = reporter

    def run_for_pattern(self, paths: Iterable[Path], extra: Extra) -> None:
        new_stage = self.__stages_factory.stage_by_command(self.__command_name)

        with typer.progressbar(
            paths,
            label=typer.style(f"→ {new_stage.name}", fg=typer.colors.CYAN),
            item_show_func=lambda x: f"  {x.name}" if x else "",
            show_pos=True,
        ) as bar:
            for path in bar:
                self.run_for_path(path, extra)

    def run_for_photoset(self, photoset: Photoset, extra: Extra) -> None:
        new_stage = self.__stages_factory.stage_by_command(self.__command_name)
        current_stage = (
            self.__stages_factory.stage_by_path(photoset.path)
            or self.__stages_factory.stub
        )

        root = self.context.world.location_of_path(photoset.path)

        self.__reporter.on_photoset_start(photoset, current_stage.name, new_stage.name)

        try:
            super().run_for_photoset(photoset, extra | {
                StageCommand.__CURRENT_STAGE: current_stage,
                StageCommand.__NEW_STAGE: new_stage,
            })

            if new_stage != current_stage:
                new_stage.transfer(photoset, root.path)

            self.__reporter.on_photoset_success(photoset, new_stage.name)
        except StageCheckError as e:
            self.__reporter.on_photoset_failure(photoset, e.problems)

    def run_for_part(self, part: Photoset, extra: Extra) -> None:
        current_stage = extra[StageCommand.__CURRENT_STAGE]
        new_stage = extra[StageCommand.__NEW_STAGE]

        current_stage.exit(part, self.__reporter)
        new_stage.enter(part, self.__reporter)


def create_stage_commands(stages_factory: StagesFactory) -> Typer:
    app = Typer()

    for stage in stages_factory.stages:
        _register_command(app, stage.command, stages_factory)

    return app


def _register_command(app: Typer, command_name: str, stages_factory: StagesFactory) -> None:
    """
    Отдельная функция чтобы command_name захватывался по значению,
    а не по ссылке из цикла.
    """

    @app.command(name=command_name)
    def stage_cmd(
            ctx: Annotated[typer.Context, Argument()],
            pattern: Annotated[List[Path], Argument()] = (Path.cwd(),),
    ) -> None:
        context: Context = ctx.obj

        StageCommand(
            context=context,
            patterns=pattern,
            command_name=command_name,
            stages_factory=stages_factory,
            reporter=TyperChecksReporter(),
        ).run()