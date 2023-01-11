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

        selector_factory = SelectorFactory(config[Config.Keys.PHOTOSET_STRUCTURE])

        extractor_factory = ExtractorFactory(selector_factory)

        checks_factory = ChecksFactory(
            selector_factory,
            extractor_factory
        )

        stages_factory = StagesFactory(
            checks_factory,
            extractor_factory
        )

        actions_factory = ActionFactory(
            stages_factory,
            checks_factory,
            ChecksRunner.instance()
        )

        self.__commands_factory = CommandFactory(stages_factory, actions_factory)

    @property
    def commands_factory(self) -> CommandFactory:
        return self.__commands_factory
