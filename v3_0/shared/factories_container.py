from v3_0.actions.action_factory import ActionFactory
from v3_0.actions.stage.logic.factories.checks_factory import ChecksFactory
from v3_0.actions.stage.logic.factories.extractor_factory import ExtractorFactory
from v3_0.actions.stage.logic.factories.selector_factory import SelectorFactory
from v3_0.actions.stage.models.stages_factory import StagesFactory
from v3_0.commands.command_factory import CommandFactory
from v3_0.shared.configuration.config import Config


class FactoriesContainer:
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

        self.__actions_factory = ActionFactory(
            stages_factory,
            checks_factory
        )

        self.__commands_factory = CommandFactory(stages_factory)

    @property
    def actions_factory(self) -> ActionFactory:
        return self.__actions_factory

    @property
    def commands_factory(self) -> CommandFactory:
        return self.__commands_factory
