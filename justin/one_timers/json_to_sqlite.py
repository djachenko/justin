from argparse import Namespace

from justin.shared.context import Context
from justin_utils.cli import Action


class JsonToSqliteAction(Action):
    def perform(self, args: Namespace, context: Context) -> None:
        people_to_update = []

        for json_person in context.cms.people:
            sqlite_person = context.sqlite_cms.get_person(json_person.folder)

            if not sqlite_person:
                print(json_person.folder)

                people_to_update.append(json_person)

        for json_person in people_to_update:
            context.sqlite_cms.register_person(
                folder=json_person.folder,
                name=json_person.name,
                vk_id=json_person.vk_id
            )
