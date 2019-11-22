from abc import abstractmethod
from argparse import Namespace

from pyvko.models.group import Group

from v3_0.shared.models.world import World


class Action:
    @abstractmethod
    def perform(self, args: Namespace, world: World, group: Group) -> None:
        pass
