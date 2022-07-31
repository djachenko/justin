import re
from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Generic, TypeVar


@dataclass(frozen=True)
class Structure:
    pass


@dataclass(frozen=True)
class XorStructure(Structure):
    options: List['Structure']


@dataclass(frozen=True)
class TopStructure(Structure):
    substructures: Dict[str, 'Structure'] = ()

    def __getitem__(self, name: str) -> Optional['Structure']:
        for pattern, substructure in self.substructures.items():
            pattern = f"^{pattern.strip('^$')}$"

            if re.search(pattern, name):
                return substructure

        return None


T = TypeVar("T")


# noinspection PyTypeChecker
class StructureVisitor(Generic[T]):
    @abstractmethod
    def visit_xor(self, structure: XorStructure) -> T:
        assert False

    @abstractmethod
    def visit_top(self, structure: TopStructure) -> T:
        assert False

    def visit_none(self) -> T:
        assert False

    def visit(self, structure: Structure) -> T:
        if structure is None:
            return self.visit_none()
        elif isinstance(structure, XorStructure):
            return self.visit_xor(structure)
        elif isinstance(structure, TopStructure):
            return self.visit_top(structure)
        else:
            print(structure.__class__.__name__)
            assert False


def parse_structure(structure_description) -> Structure:
    if isinstance(structure_description, list):
        return XorStructure(options=[parse_structure(option) for option in structure_description])
    elif isinstance(structure_description, dict):
        return TopStructure(substructures={
            pattern: parse_structure(substructure_description)
            for pattern, substructure_description
            in structure_description.items()
        })
    else:
        assert False
