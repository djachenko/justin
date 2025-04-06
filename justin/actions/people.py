from argparse import ArgumentParser, Namespace
from typing import List

from justin.actions.destinations_aware_action import DestinationsAwareAction
from justin.actions.pattern_action import Extra
from justin.cms.people_cms import PeopleCMS, PersonEntry
from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin.shared.metafile import MetaFolder
from justin_utils.cli import Action, Parameter
from pyvko.pyvko_main import Pyvko


class RegisterPeopleAction(DestinationsAwareAction):
    def handle_closed(self, closed_folder: MetaFolder, context: Context, extra: Extra) -> None:
        super().handle_closed(closed_folder, context, extra)

        self.__register_from_path(closed_folder, context.pyvko, context.cms, extra[RegisterPeopleAction.SET_NAME])

    def handle_drive(self, drive_folder: MetaFolder, context: Context, extra: Extra) -> None:
        super().handle_drive(drive_folder, context, extra)

        self.__register_from_path(drive_folder, context.pyvko, context.cms, extra[RegisterPeopleAction.SET_NAME])

    def handle_my_people(self, my_people_folder: MetaFolder, context: Context, extra: Extra) -> None:
        super().handle_my_people(my_people_folder, context, extra)

        self.__register_from_path(
            my_people_folder,
            context.pyvko,
            context.cms,
            extra[RegisterPeopleAction.SET_NAME]
        )

    def handle_common(self, folder: MetaFolder, context: Context, extra: Extra) -> None:
        pass

    @staticmethod
    def __register_from_path(tree: Folder, pyvko: Pyvko, register: PeopleCMS, source: str) -> None:
        for my_person in tree.subfolders:
            register.register_person(my_person.path, source, pyvko)


class FixPeopleAction(Action):
    def configure_subparser(self, subparser: ArgumentParser) -> None:
        super().configure_subparser(subparser)

        group_adder = subparser.add_mutually_exclusive_group(required=True)

        group_adder.add_argument("--all", action="store_true")
        group_adder.add_argument("--name")
        # group_adder.add_argument("--by", "-by", type=Path, default=Path.cwd().as_posix())

    def perform(self, args: Namespace, context: Context) -> None:
        register = context.cms.people

        if args.all:
            print("all")
            people_to_fix = [i for i in register]
        elif args.name:
            people_to_fix = [register.get(args.name)]
        else:
            assert False

        people_to_fix = [person for person in people_to_fix if not PersonEntry.is_valid(person, strict=True)]

        if not people_to_fix:
            print("Fixing not needed.")

            return

        for person in people_to_fix:
            context.cms.fix_person(person, context.pyvko)


class SpecifyPersonAction(Action):

    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter("folder"),
            Parameter("postfix"),
        ]

    def perform(self, args: Namespace, context: Context) -> None:
        context.cms.migrate_person(args.folder, f"{args.folder}_{args.postfix}")
