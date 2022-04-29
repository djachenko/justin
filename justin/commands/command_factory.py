from functools import lru_cache
from typing import List

from justin.actions.action_factory import ActionFactory
from justin.actions.named.stage.models.stages_factory import StagesFactory
from justin.commands.command import Command
from justin.commands.single_subparser_commands.named_command import NamedCommand
from justin.commands.stage_command import StageCommand
from justin_utils.cli import Command as CLICommand


class CommandFactory:
    def __init__(self, stages_factory: StagesFactory, action_factory: ActionFactory) -> None:
        super().__init__()

        self.__stages_factory = stages_factory
        self.__action_factory = action_factory

    @lru_cache()
    def commands(self) -> List[Command]:
        return [
            StageCommand(self.__action_factory.stage_action(), self.__stages_factory),

            CLICommand(
                "upload",
                [
                    self.__action_factory.web_sync_action(),
                    self.__action_factory.upload_action(),
                    self.__action_factory.rearrange_action(),
                ],
                allowed_same_parameters=[
                    "pattern",
                ]
            ),

            CLICommand("delete_posts", [self.__action_factory.delete_posts_action()]),

            CLICommand("rearrange", [self.__action_factory.rearrange_action()]),
            CLICommand("delay", [self.__action_factory.delay_action()]),
            CLICommand("resize_gif_sources", [self.__action_factory.resize_gif_action()]),

            NamedCommand("local_sync", self.__action_factory.local_sync_action()),
            NamedCommand("archive", self.__action_factory.archive_action()),
            CLICommand("move", [self.__action_factory.move_action()]),
            CLICommand("make_gif", [self.__action_factory.make_gif_action()]),
            CLICommand("split", [self.__action_factory.split_action()]),
            CLICommand("fix_metafile", [self.__action_factory.fix_metafile_action()]),
            CLICommand("web_sync", [self.__action_factory.web_sync_action()]),
            CLICommand("check_ratios", [self.__action_factory.check_ratios()]),
            CLICommand("sequence", [self.__action_factory.sequence()]),

        ]
