from argparse import Namespace
from pathlib import Path

from justin.actions.named.named_action import NamedAction, Context, Extra
from justin.shared.helpers.checks_runner import ChecksRunner
from justin.shared.models.photoset import Photoset
from justin.shared.place import Place


class RelocateAction(NamedAction):
    def __init__(self) -> None:
        super().__init__()

        self.__checks_runner = ChecksRunner.instance()

    def place_by_command(self, command: str) -> Place:
        pass

    def place_by_path(self, path: Path) -> Place:
        pass

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        new_place = self.place_by_command(args.command)
        old_place = self.place_by_path(photoset.path)

        transfer_checks = old_place.outcoming_checks + new_place.incoming_checks

        for hook in old_place.hooks:
            hook.backwards(photoset)

        self.__checks_runner.run(photoset, checks=transfer_checks)

        if new_place != old_place:
            photoset_to_old_place = photoset.path.relative_to(old_place.path)
            new_photoset_path = new_place.path / photoset_to_old_place

            photoset.move(new_photoset_path)

        for hook in new_place.hooks:
            hook.forward(photoset)
