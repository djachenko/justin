from argparse import ArgumentParser, Namespace
from typing import List

from justin.actions.destinations_aware_action import DestinationsAwareAction
from justin.actions.pattern_action import Extra
from justin.cms.people_cms import PersonEntry
from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin_utils import util
from justin_utils.cli import Action, Parameter
from pyvko.aspects.groups import Group
from pyvko.entities.user import User
from pyvko.pyvko_main import Pyvko


class RegisterPeopleAction(DestinationsAwareAction):
    def handle_closed(self, closed_folder: Folder, context: Context, extra: Extra) -> None:
        RegisterPeopleAction.__register_from_path(
            closed_folder,
            context
        )

    def handle_drive(self, drive_folder: Folder, context: Context, extra: Extra) -> None:
        RegisterPeopleAction.__register_from_path(
            drive_folder,
            context
        )

    def handle_my_people(self, my_people_folder: Folder, context: Context, extra: Extra) -> None:
        RegisterPeopleAction.__register_from_path(
            my_people_folder,
            context
        )

    def handle_common(self, folder: Folder, context: Context, extra: Extra) -> None:
        pass

    @staticmethod
    def __register_from_path(folder_with_people: Folder, context: Context) -> None:
        for person_folder in folder_with_people.subfolders:
            vk_entity = RegisterPeopleAction.__get_vk_entity(person_folder.name, context.pyvko)

            context.sqlite_cms.register_person(
                folder=person_folder.name,
                name=vk_entity.name,
                vk_id=vk_entity.id
            )

    @staticmethod
    def __get_vk_entity(folder: str, pyvko: Pyvko) -> User | Group | None:
        abort = None
        empty = ""

        choice = util.ask_for_choice_flagged(f"Who is {folder} in vk?", [])

        if choice == abort or choice == empty:
            return None
        else:
            return pyvko.get(choice)


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
