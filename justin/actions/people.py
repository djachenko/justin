from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List

from justin.actions.named.destinations_aware_action import DestinationsAwareAction
from justin.actions.pattern_action import Extra
from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin.shared.models.person import PeopleRegister, Person
from justin.shared.models.photoset import Photoset
from justin_utils import util
from justin_utils.cli import Action, Parameter
from pyvko.entities.user import User
from pyvko.pyvko_main import Pyvko


class FixPeopleMixin:
    @staticmethod
    def fix_person(person: Person, register: PeopleRegister, pyvko: Pyvko) -> None:

        folder = person.folder

        if not person.vk_id:
            url = input(f"Who is {folder} in vk? ")

            if url == "-":
                return
        else:
            url = input(f"Who is {folder} in vk? ") or person.vk_id

        user: User = pyvko.get(url)

        assert isinstance(user, User)

        vk_id = user.id
        vk_name = f"{user.first_name} {user.last_name}"

        if not person.name:
            new_name = input(f"Is it {vk_name}? (empty - yes, any string - new name) ") or vk_name
        else:
            other = "other"

            new_name = util.ask_for_choice(f"Who is {person.folder}?", [
                person.name,
                vk_name,
                other
            ])

            if new_name == other:
                while True:
                    new_name = input("Who then?")

                    if new_name:
                        break

        person.vk_id = vk_id
        person.name = new_name

        register.update_person(person)


class RegisterPeopleAction(DestinationsAwareAction, FixPeopleMixin):
    def handle_closed(self, closed_folder: Folder, context: Context, extra: Extra) -> None:
        super().handle_closed(closed_folder, context, extra)

        self.__register_from_path(closed_folder, context.pyvko, context.closed)

    def handle_my_people(self, my_people_folder: Folder, context: Context, extra: Extra) -> None:
        super().handle_my_people(my_people_folder, context, extra)

        self.__register_from_path(my_people_folder, context.pyvko, context.my_people)

    def handle_common(self, folder: Folder, context: Context, extra: Extra) -> None:
        pass

    def __register_from_path(self, tree: Folder, pyvko: Pyvko, register: PeopleRegister):
        for my_person in tree.subfolders:
            if my_person.name in register:
                continue

            self.fix_person(
                Person(
                    vk_id=None,
                    name=None,
                    folder=my_person.stem,
                    source=tree.name,
                ),
                register,
                pyvko
            )


class FixPeopleAction(Action, FixPeopleMixin):
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

            names_in_folder = {name_tree.name for name_tree in names_root.subfolders}

            registered_people = [register.get_by_folder(name) for name in names_in_folder]
            people_to_fix = filter(None, registered_people)

            names_to_register = filter(lambda x: x not in register, names_in_folder)

            if names_to_register:
                print(", ".join(names_to_register), "won't be fixed, need to be registered.")
        else:
            assert False

        print(len(list(people_to_fix)))

        people_to_fix = [person for person in people_to_fix if not Person.is_valid(person)]

        print(len(list(people_to_fix)))

        if not people_to_fix:
            print("Fixing not needed.")

            return

        for person in people_to_fix:
            self.fix_person(person, register, context.pyvko)
