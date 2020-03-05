from functools import lru_cache
from typing import List

from v3_0.actions.action_id import ActionId
from v3_0.actions.named.stage.models.stages_factory import StagesFactory
from v3_0.commands.command import Command
from v3_0.commands.single_subparser_commands.delay_command import DelayCommand
from v3_0.commands.single_subparser_commands.resize_gif_sources_command import ResizeGifSourcesCommand
from v3_0.commands.single_subparser_commands.single_action_command import SingleActionCommand
from v3_0.commands.single_subparser_commands.delete_posts_command import DeletePostsCommand
from v3_0.commands.single_subparser_commands.named_command import NamedCommand
from v3_0.commands.single_subparser_commands.rearrange_command import RearrangeCommand
from v3_0.commands.single_subparser_commands.upload_command import UploadCommand
from v3_0.commands.stage_command import StageCommand


class CommandFactory:
    def __init__(self, stages_factory: StagesFactory) -> None:
        super().__init__()

        self.__stages_factory = stages_factory

    @lru_cache()
    def commands(self) -> List[Command]:
        return [
            StageCommand(self.__stages_factory),
            UploadCommand(),
            DeletePostsCommand(),
            RearrangeCommand(),
            SingleActionCommand("local_sync", ActionId.LOCAL_SYNC),
            NamedCommand("archive", ActionId.ARCHIVE),
            NamedCommand("move", ActionId.MOVE),
            NamedCommand("make_gif", ActionId.MAKE_GIF),
            NamedCommand("split", ActionId.SPLIT),
            NamedCommand("fix_metafile", ActionId.FIX_METAFILE),
            SingleActionCommand("web_sync", ActionId.SYNC_POSTS_STATUS),
            DelayCommand(),
            ResizeGifSourcesCommand(),
        ]
