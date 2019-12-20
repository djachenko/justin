from functools import lru_cache
from typing import List

from v3_0.actions.stage.models.stages_factory import StagesFactory
from v3_0.commands.single.named.archive_command import ArchiveCommand
from v3_0.commands.command import Command
from v3_0.commands.single.delete_posts_command import DeletePostsCommand
from v3_0.commands.single.local_sync_command import LocalSyncCommand
from v3_0.commands.single.named.make_gifs_command import MakeGifCommand
from v3_0.commands.single.named.move_command import MoveCommand
from v3_0.commands.single.rearrange_command import RearrangeCommand
from v3_0.commands.stage_command import StageCommand
from v3_0.commands.single.upload_command import UploadCommand


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
            MakeGifCommand(),
        ]
