import json
from pathlib import Path
from typing import Dict, Type, List

from justin.shared.metafiles.metafile import RootMetafile, V, MetafileReadWriter
from justin.shared.metafiles.migrations import MetafileMigrator


class MetafileReadWriterImpl(MetafileReadWriter):
    def __init__(self, migrator: MetafileMigrator, *types: Type[RootMetafile]) -> None:
        super().__init__()

        self.__mapping: Dict[str, Type[RootMetafile]] = {}

        for type_ in types:
            assert type_.type() not in self.__mapping

            self.__mapping[type_.type()] = type_

        self.__migrator = migrator

    def read(self, path: Path, metafile_type: V = None) -> V | None:
        metafiles = self.read_all(path)

        if len(metafiles) == 0:
            return None

        if len(metafiles) == 1 and metafile_type is None:
            return metafiles[0]

        for metafile in metafiles:
            if type(metafile) == metafile_type:
                return metafile

        return None

    def read_all(self, path: Path) -> List[V]:
        self.__migrator.migrate_path(path)

        if not path.exists() or path.stat().st_size <= 0:
            return []

        with path.open() as metafile_file:
            json_dict = json.load(metafile_file)

        metafiles = []

        for metafile_type in json_dict:
            if metafile_type not in self.__mapping:
                a = 7

            assert metafile_type in self.__mapping

            metafile_type = self.__mapping[metafile_type]

            metafile = metafile_type.from_json(json_dict[metafile_type.type()])

            metafiles.append(metafile)

        return metafiles

    # noinspection PyMethodMayBeStatic
    def write(self, metafile: RootMetafile, path: Path) -> None:
        if path.exists():
            with path.open() as metafile_file:
                metafile_json = json.load(metafile_file)
        else:
            metafile_json = {}

        metafile_json[metafile.type()] = metafile.as_json()

        with path.open(mode="w") as metafile_file:
            json.dump(metafile_json, metafile_file, indent=4)
