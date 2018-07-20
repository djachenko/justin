from filesystem2.path import Path


class RelativePath(Path):
    pass

    def end_of(self, path: Path) -> bool:
        if len(self.parts) > len(path.parts):
            return False

        reversed_own_parts = reversed(self.parts)
        reversed_other_parts = reversed(path.parts)

        zipped = zip(reversed_own_parts, reversed_other_parts)

        comparison_result = [own_part == other_part for own_part, other_part in zipped]

        return all(comparison_result)
