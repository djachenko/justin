from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List

from justin.actions.named.destinations_aware_action import DestinationsAwareAction
from justin.actions.pattern_action import Extra
from justin.shared.context import Context
from justin.shared.filesystem import FolderTree
from justin.shared.models.person import PeopleRegister, Person
from justin.shared.models.photoset import Photoset
from justin_utils.cli import Action, Parameter
from pyvko.entities.user import User
from pyvko.pyvko_main import Pyvko


class RegisterPeopleAction(DestinationsAwareAction):
    def handle_closed(self, closed_folder: FolderTree, context: Context, extra: Extra) -> None:
        super().handle_closed(closed_folder, context, extra)

        self.__register_from_path(closed_folder, context.pyvko, context.closed)

    def handle_my_people(self, my_people_folder: FolderTree, context: Context, extra: Extra) -> None:
        super().handle_my_people(my_people_folder, context, extra)

        self.__register_from_path(my_people_folder, context.pyvko, context.my_people)

    def handle_common(self, folder: FolderTree, context: Context, extra: Extra) -> None:
        pass

    @staticmethod
    def __register_from_path(tree: FolderTree, pyvko: Pyvko, register: PeopleRegister):

        source = tree.name

        for my_person in tree.subtrees:
            if my_person.name in register:
                continue

            url = input(f"Who is {my_person.name}? ")

            if url == "-":
                continue

            user: User = pyvko.get(url)

            assert isinstance(user, User)

            vk_id = user.id
            name = f"{user.first_name} {user.last_name}"

            person = Person(
                vk_id=vk_id,
                name=name,
                folder=my_person.stem,
                source=source,
            )

            register.add_person(person)


class FixPeopleAction(Action):
    MY_PEOPLE_FLAG = "my_people"
    CLOSED_FLAG = "closed"

    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter(
                flags=[
                    "--type",
                    "-t"
                ],
                choices=[
                    FixPeopleAction.MY_PEOPLE_FLAG,
                    FixPeopleAction.CLOSED_FLAG,
                ],
                default=FixPeopleAction.MY_PEOPLE_FLAG
            )
        ]

    def configure_subparser(self, subparser: ArgumentParser) -> None:
        super().configure_subparser(subparser)

        group_adder = subparser.add_mutually_exclusive_group(required=True)

        group_adder.add_argument("--all", "-a", action="store_true")
        group_adder.add_argument("--name", "-n")
        group_adder.add_argument("--by", type=Path, default=Path.cwd().as_posix())

    def perform(self, args: Namespace, context: Context) -> None:
        selected_type = args.type

        if selected_type == FixPeopleAction.MY_PEOPLE_FLAG:
            register = context.my_people
        elif selected_type == FixPeopleAction.CLOSED_FLAG:
            register = context.closed
        else:
            assert False

        if args.all:
            print("all")
            people_to_fix = [i for i in register]
        elif args.name:
            people_to_fix = [register.get_by_folder(args.name)]
        elif args.by:
            photoset = Photoset.from_path(args.by)

            if selected_type == FixPeopleAction.MY_PEOPLE_FLAG:
                names_root = photoset.my_people
            elif selected_type == FixPeopleAction.CLOSED_FLAG:
                names_root = photoset.closed
            else:
                assert False

            names_in_folder = {name_tree.name for name_tree in names_root.subtrees}

            registered_people = [register.get_by_folder(name) for name in names_in_folder]
            people_to_fix = filter(None, registered_people)

            names_to_register = filter(lambda x: x not in register, names_in_folder)

            if names_to_register:
                print(", ".join(names_to_register), "won't be fixed, need to be registered.")
        else:
            assert False

        print(len(list(people_to_fix)))

        people_to_fix = filter(lambda x: not Person.is_valid(x), people_to_fix)

        print(len(list(people_to_fix)))


        if not people_to_fix:
            print("Fixing not needed.")

        for person in people_to_fix:
            folder = person.folder

            person.vk_id = input(f"Enter {folder}'s vk_id (current {person.vk_id}):") or person.vk_id
            person.name = input(f"Enter {folder}'s name (current {person.name}):") or person.name

            register.fix_person(person)
