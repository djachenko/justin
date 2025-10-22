import json
from abc import abstractmethod
from dataclasses import fields
from pathlib import Path
from typing import Type

from justin.shared.helpers.utils import Json
from justin.shared.metafiles.metafile import GroupMetafile, RootMetafile


class MetafileMigration:
    @abstractmethod
    def accepts(self, json_object: Json) -> bool:
        pass

    @abstractmethod
    def migrate(self, json_object: Json) -> Json:
        pass


class NegativeGroupIdMigration(MetafileMigration):
    def accepts(self, json_dict: Json) -> bool:
        if "type" not in json_dict:
            return False

        if GroupMetafile.type() not in json_dict["type"]:
            return False

        return True

    def migrate(self, json_dict: Json) -> Json:
        json_dict["group_id"] = -abs(json_dict["group_id"])

        return json_dict


class NewStructureMigration(MetafileMigration):
    def __init__(self, *types: Type[RootMetafile]):
        super().__init__()

        self.metafiles = {type_.type(): fields(type_) for type_ in types}

    def accepts(self, json_object: Json) -> bool:
        return "type" in json_object

    def migrate(self, json_object: Json) -> Json:
        result = {}

        for type_ in json_object["type"]:
            fieldset = self.metafiles[type_]

            if "location_order" in fieldset:
                a = 7

            new_dict = {field.name: json_object.get(field.name, field.default) for field in fieldset}

            result[type_] = new_dict

        return result


class MetafileMigrator:
    def __init__(self, *migrations: MetafileMigration) -> None:
        super().__init__()

        self.__migrations = migrations

    def migrate_path(self, path: Path) -> None:
        if not path.exists() or path.stat().st_size <= 0:
            return

        json_dict = {}

        with path.open() as metafile_file:
            json_dict = json.load(metafile_file)

        modified = False

        for migration in self.__migrations:
            if migration.accepts(json_dict):
                json_dict = migration.migrate(json_dict.copy())

                modified = True

        if modified:
            with path.open(mode="w") as metafile_file:
                json.dump(json_dict, metafile_file, indent=4)
