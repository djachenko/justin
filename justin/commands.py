from argparse import ArgumentParser
from functools import lru_cache
from typing import List, Iterable

from justin.actions.action_factory import ActionFactory
from justin.actions.named.stage.models.stages_factory import StagesFactory
from justin_utils.cli import Command, Action


class SingleActionCommand(Command):
    def __init__(self, name: str, action: Action, allowed_same_parameters: Iterable[str] = ()) -> None:
        super().__init__(name, [action], allowed_same_parameters)


class StageCommand(SingleActionCommand):
    def configure_subparser(self, subparser: ArgumentParser) -> None:
        super().configure_subparser(subparser)

        subparser.set_defaults(command_name=self.name)


class CommandFactory:
    def __init__(self, stages_factory: StagesFactory, action_factory: ActionFactory) -> None:
        super().__init__()

        self.__stages_factory = stages_factory
        self.__action_factory = action_factory

    @lru_cache()
    def commands(self) -> List[Command]:
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
                    self.__action_factory.rearrange_action(),
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
            SingleActionCommand("panext", self.__action_factory.pano_extract()),
        ]
