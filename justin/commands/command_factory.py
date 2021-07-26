from functools import lru_cache
from typing import List

from justin.actions.action_factory import ActionFactory
from justin.actions.named.stage.models.stages_factory import StagesFactory
from justin.commands.command import Command
from justin.commands.single_subparser_commands.delay_command import DelayCommand
from justin.commands.single_subparser_commands.delete_posts_command import DeletePostsCommand
from justin.commands.single_subparser_commands.named_command import NamedCommand
from justin.commands.single_subparser_commands.rearrange_command import RearrangeCommand
from justin.commands.single_subparser_commands.resize_gif_sources_command import ResizeGifSourcesCommand
from justin.commands.single_subparser_commands.upload_command import UploadCommand
from justin.commands.stage_command import StageCommand


class CommandFactory:
    def __init__(self, stages_factory: StagesFactory, action_factory: ActionFactory) -> None:
        super().__init__()

        self.__stages_factory = stages_factory
        self.__action_factory = action_factory

    @lru_cache()
    def commands(self) -> List[Command]:
        return [
            StageCommand(self.__action_factory.stage_action(), self.__stages_factory),

            UploadCommand([
                self.__action_factory.web_sync_action(),
                self.__action_factory.schedule_action(),
                self.__action_factory.rearrange_action(),
            ]),

            DeletePostsCommand(self.__action_factory.delete_posts_action()),
            RearrangeCommand(self.__action_factory.rearrange_action()),
            DelayCommand(self.__action_factory.delay_action()),
            ResizeGifSourcesCommand(self.__action_factory.resize_gif_action()),

            NamedCommand("local_sync", self.__action_factory.local_sync_action()),
            NamedCommand("archive", self.__action_factory.archive_action()),
            NamedCommand("move", self.__action_factory.move_action()),
            NamedCommand("make_gif", self.__action_factory.make_gif_action()),
            NamedCommand("split", self.__action_factory.split_action()),
            NamedCommand("fix_metafile", self.__action_factory.fix_metafile_action()),
            NamedCommand("web_sync", self.__action_factory.web_sync_action()),
        ]
