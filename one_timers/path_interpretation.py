from pathlib import Path

from v3_0.shared import structure


class PathInterpretation:
    def __init__(self, disk: str, photos: str, destination: str, category: str, set_name: str) -> None:
        super().__init__()

        self.disk = disk
        self.photos = photos
        self.destination = destination
        self.category = category
        self.set_name = set_name

    @staticmethod
    def interpret(path: Path) -> 'PathInterpretation':
        parts = list(path.parts)

        disk = parts[0]
        photos = parts[1]
        destination = parts[2]

        disk_structure = structure.disk_structure

        if disk_structure[parts[2]].has_implicit_sets:
            parts.insert(3, "")

        category = parts[3]
        set_name = parts[4]

        interpretation = PathInterpretation(
            disk,
            photos,
            destination,
            category,
            set_name
        )

        return interpretation
