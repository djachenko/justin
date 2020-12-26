from abc import abstractmethod
from argparse import Namespace

from pyvko.models.group import Group

from justin.shared.models.world import World


class Action:
    @abstractmethod
    def perform(self, args: Namespace, world: World, group: Group) -> None:
        pass
