from functools import lru_cache
from typing import List

from v3_0.actions.stage.models.stages_factory import StagesFactory
from v3_0.commands.archive_command import ArchiveCommand
from v3_0.commands.command import Command
from v3_0.commands.delete_posts_command import DeletePostsCommand
from v3_0.commands.local_sync_command import LocalSyncCommand
from v3_0.commands.move_command import MoveCommand
from v3_0.commands.rearrange_command import RearrangeCommand
from v3_0.commands.stage_command import StageCommand
from v3_0.commands.upload_command import UploadCommand


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
            LocalSyncCommand(),
            ArchiveCommand(),
            MoveCommand(),
        ]
