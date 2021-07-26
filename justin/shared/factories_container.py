from justin.actions.action_factory import ActionFactory
from justin.actions.named.stage.logic.factories.checks_factory import ChecksFactory
from justin.actions.named.stage.logic.factories.extractor_factory import ExtractorFactory
from justin.actions.named.stage.logic.factories.selector_factory import SelectorFactory
from justin.actions.named.stage.models.stages_factory import StagesFactory
from justin.commands.command_factory import CommandFactory
from justin.shared.config import Config


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

        actions_factory = ActionFactory(
            stages_factory,
            checks_factory
        )

        self.__commands_factory = CommandFactory(stages_factory, actions_factory)

    @property
    def commands_factory(self) -> CommandFactory:
        return self.__commands_factory
