from functools import lru_cache
from typing import Iterable

from justin.commands import SingleActionCommand, StageCommand
from justin.di.actions import ActionFactory
from justin.di.stages import StagesFactory
from justin_utils.cli import Command


class CommandFactory:
    def __init__(self, stages_factory: StagesFactory, action_factory: ActionFactory) -> None:
        super().__init__()

        self.__stages_factory = stages_factory
        self.__action_factory = action_factory

    @lru_cache()
    def commands(self) -> Iterable[Command]:
        stage_commands = [
            StageCommand(stage.command, self.__action_factory.stage_action())
            for stage in self.__stages_factory.stages()
        ]

        return stage_commands + [
            Command(
                "upload",
                [
                    self.__action_factory.web_sync_action(),
                    self.__action_factory.upload_action(),
                ],
                allowed_same_parameters=[
                    "pattern",
                ]
            ),

            SingleActionCommand("delete_posts", self.__action_factory.delete_posts_action()),
            SingleActionCommand("rearrange", self.__action_factory.rearrange_action()),
            SingleActionCommand("delay", self.__action_factory.delay_action()),
            SingleActionCommand("resize_gif_sources", self.__action_factory.resize_gif_action()),
            SingleActionCommand("move", self.__action_factory.move_action()),
            SingleActionCommand("make_gif", self.__action_factory.make_gif_action()),
            SingleActionCommand("split", self.__action_factory.split_action()),
            SingleActionCommand("fix_metafile", self.__action_factory.fix_metafile_action()),
            SingleActionCommand("web_sync", self.__action_factory.web_sync_action()),
            SingleActionCommand("check_ratios", self.__action_factory.check_ratios()),
            SingleActionCommand("sequence", self.__action_factory.sequence()),
            SingleActionCommand("create_event", self.__action_factory.create_event()),
            SingleActionCommand("setup_event", self.__action_factory.setup_event()),
            SingleActionCommand("group", self.__action_factory.date_split()),
            SingleActionCommand("reg_people", self.__action_factory.register_people()),
            SingleActionCommand("fix_people", self.__action_factory.fix_people()),
            SingleActionCommand("drone", self.__action_factory.drone()),
            SingleActionCommand("cms", self.__action_factory.cms()),
            SingleActionCommand("location", self.__action_factory.location()),
        ]
