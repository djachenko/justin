from abc import abstractmethod
from argparse import Namespace

from justin.shared.context import Context


class Action:
    @abstractmethod
    def perform(self, args: Namespace, context: Context) -> None:
        pass
