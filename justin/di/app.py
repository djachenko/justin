from functools import cache

from lazy_object_proxy import Proxy

from justin.shared.config import Config
from justin.di.actions import ActionFactory
from justin.di.checks import ChecksFactory
from justin.di.commands import CommandFactory
from justin.di.extractors import ExtractorFactory
from justin.di.selectors import SelectorFactory
from justin.di.stages import StagesFactory
from justin.shared.helpers.checks_runner import ChecksRunner


class DI:
    def __init__(self, config: Config) -> None:
        super().__init__()

        self.__selector_factory_ = Proxy(lambda: SelectorFactory(config[Config.Keys.PHOTOSET_STRUCTURE]))

    @property
    @cache
    def __selector_factory(self) -> SelectorFactory:
        return self.__selector_factory_

    @property
    @cache
    def __extractor_factory(self):
        return ExtractorFactory(
            self.__selector_factory
        )

    @property
    @cache
    def __checks_factory(self) -> ChecksFactory:
        return ChecksFactory(
            self.__selector_factory,
            self.__extractor_factory
        )

    @property
    @cache
    def __stages_factory(self) -> StagesFactory:
        return StagesFactory(
            self.__checks_factory,
            self.__extractor_factory
        )

    @property
    @cache
    def __actions_factory(self) -> ActionFactory:
        return ActionFactory(
            self.__stages_factory,
            self.__checks_factory,
            self.__checks_runner
        )

    @property
    @cache
    def __checks_runner(self) -> ChecksRunner:
        return ChecksRunner()

    @property
    @cache
    def commands_factory(self) -> CommandFactory:
        return CommandFactory(
            self.__stages_factory,
            self.__actions_factory
        )
