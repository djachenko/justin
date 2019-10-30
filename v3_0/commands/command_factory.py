from functools import lru_cache
from typing import List

from v3_0.actions.stage.models.stages_factory import StagesFactory
from v3_0.commands.command import Command
from v3_0.commands.delete_posts_command import DeletePostsCommand
from v3_0.commands.local_sync_command import LocalSyncCommand
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
            self.stage(),
            self.upload(),
            self.delete_posts(),
            self.rearrange(),
            self.local_sync(),
        ]

    @lru_cache()
    def stage(self) -> Command:
        return StageCommand(self.__stages_factory)

    @lru_cache()
    def upload(self) -> Command:
        return UploadCommand()

    @lru_cache()
    def rearrange(self) -> Command:
        return RearrangeCommand()

    @lru_cache()
    def delete_posts(self) -> Command:
        return DeletePostsCommand()

    @lru_cache()
    def local_sync(self) -> Command:
        return LocalSyncCommand()
