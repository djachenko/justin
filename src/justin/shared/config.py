from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any

from justin.shared.structure import Structure


@dataclass(frozen=True)
class Config:
    justin_url: str
    closed_url: str
    meeting_url: str
    kot_i_kit_url: str
    my_people_url: str
    cullen_url: str

    spreadsheet_id: str

    photoset_structure: Structure
    # disk_structure: Structure

    @staticmethod
    def from_source(path: Path, init_globals: Dict[str, Any] = None) -> 'Config':
        import importlib.util
        spec = importlib.util.spec_from_file_location("config", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        config_dict = module.build_config(**init_globals)

        return config_dict

