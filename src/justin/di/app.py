from functools import cached_property

from lazy_object_proxy import Proxy

from justin.di.metafiles import setup_metafiles
from justin.shared.config import Config
from justin.typer.stage_command.checks_factory import ChecksFactory
from justin.typer.stage_command.hooks_factory import HooksFactory
from justin.typer.stage_command.stages_factory import StagesFactory


class DI:
    def __init__(self, config: Config) -> None:
        super().__init__()

        self.__checks_factory = Proxy(lambda: ChecksFactory(config.photoset_structure))

        setup_metafiles()

    @cached_property
    def __hooks_factory(self):
        return HooksFactory()

    @cached_property
    def stages_factory(self) -> StagesFactory:
        return StagesFactory(
            self.__checks_factory,
            self.__hooks_factory
        )
