from pathlib import Path
from typing import Annotated, List

import typer
from justin_utils import util
from typer import Typer, Argument

from justin.typer.base_commands.pattern_command import Extra
from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin.typer.base_commands.destinations_aware_command import DestinationsAwareCommand
from pyvko.aspects.groups import Group
from pyvko.entities.user import User
from pyvko.pyvko_main import Pyvko


class RegisterPeopleCommand(DestinationsAwareCommand):
    def handle_closed(self, closed_folder: Folder, extra: Extra) -> None:
        RegisterPeopleCommand._register_from_path(
            closed_folder,
            self.context
        )
    
    def handle_drive(self, drive_folder: Folder, extra: Extra) -> None:
        RegisterPeopleCommand._register_from_path(
            drive_folder,
            self.context
        )
    
    def handle_my_people(self, my_people_folder: Folder, extra: Extra) -> None:
        RegisterPeopleCommand._register_from_path(
            my_people_folder,
            self.context
        )
    
    def handle_common(self, folder: Folder, extra: Extra) -> None:
        pass
    
    @staticmethod
    def _register_from_path(folder_with_people: Folder, context: Context) -> None:
        for person_folder in folder_with_people.subfolders:
            if context.sqlite_cms.get_person(person_folder.name):
                continue

            vk_entity = RegisterPeopleCommand._get_vk_entity(person_folder.name, context.pyvko)

            if not vk_entity:
                vk_name = RegisterPeopleCommand._ask_name(person_folder.name)
                vk_id = None
            elif isinstance(vk_entity, User):
                vk_name = f"{vk_entity.first_name} {vk_entity.last_name}"
                vk_id = vk_entity.id
            elif isinstance(vk_entity, Group):
                vk_name = vk_entity.name
                vk_id = vk_entity.id
            else:
                assert False

            context.sqlite_cms.register_person(
                folder=person_folder.name,
                name=vk_name,
                vk_id=vk_id
            )
    
    @staticmethod
    def _get_vk_entity(folder: str, pyvko: Pyvko) -> User | Group | None:
        abort = None
        empty = ""

        choice = util.ask_for_choice_flagged(f"Who is {folder} in vk?", [])

        if choice == abort or choice == empty:
            return None
        else:
            return pyvko.get(choice)
    
    @staticmethod
    def _ask_name(folder_name: str) -> str:
        return input(f"What is {folder_name}'s name?\n> ")


app = Typer()


@app.command()
def reg_people(
    context: Annotated[typer.Context, Argument()],
    pattern: Annotated[List[Path], Argument()] = (Path.cwd(),)
) -> None:
    RegisterPeopleCommand(context.obj, pattern).run()


