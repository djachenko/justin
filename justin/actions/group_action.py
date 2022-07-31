from abc import abstractmethod, ABC
from argparse import Namespace
from typing import List

from pyvko.models.active_models import Group

from justin_utils.cli import Action, Parameter, Context


class GroupAction(Action, ABC):
    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter("--group", choices=[
                "justin",
                "kotikit"
            ]),
        ]

    def perform(self, args: Namespace, context: Context) -> None:
        if not hasattr(args, "group") or args.group is None:
            group = context.default_group
        elif args.group == "justin":
            group = context.justin_group
        elif args.group == "kotikit":
            group = context.kot_i_kit_group
        else:
            assert False

        self.perform_for_group(group, args, context)

    @abstractmethod
    def perform_for_group(self, group: Group, args: Namespace, context: Context) -> None:
        pass
