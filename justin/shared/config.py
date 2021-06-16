import runpy
from enum import Enum
from pathlib import Path
from typing import Union

from justin.shared.structure import Structure


class Config:
    class Keys(str, Enum):
        GROUP_URL = "group_url"
        PYVKO_CONFIG = "pyvko_config"
        PHOTOSET_STRUCTURE = "photoset_structure"
        DISK_STRUCTURE = "global_structure"

    def __init__(self, json_object: dict) -> None:
        super().__init__()

        self.__internal_dict = {key: json_object[key] for key in Config.Keys}

        self.__internal_dict[Config.Keys.PYVKO_CONFIG] = Path(self.__internal_dict[Config.Keys.PYVKO_CONFIG])

    def __getitem__(self, key: Keys) -> Union[str, Path, Structure]:
        return self.__internal_dict[key]

    @staticmethod
    def from_source(path: Path) -> 'Config':
        run_result = runpy.run_path(str(path))

        config_dict = run_result["config"]

        return Config(config_dict)
