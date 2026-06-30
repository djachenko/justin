import json
from abc import ABC
from functools import cached_property
from pathlib import Path
from typing import Iterable, Dict, Any

from frozendict import frozendict

from justin.actions.pattern_action import Extra
from justin.shared.context import Context
from justin.shared.models.photoset import Photoset
from justin_utils.filesystem import Folder


class PatternCommand(ABC):
    SET_NAME = "set_name"
    PART_FULL_NAME = "part_full_name"

    @cached_property
    def extra(self) -> Extra:
        return frozendict()

    @property
    def context(self) -> Context:
        return self.__context

    def __init__(self, context: Context, patterns: Iterable[Path]):
        self.__patterns = patterns
        self.__context = context

    def run(self) -> None:
        paths = self.__patterns

        if not any(paths):
            print("No items found for that pattern.")

            return

        self.run_for_pattern(paths, self.extra)

    def run_for_pattern(self, paths: Iterable[Path], extra: Extra) -> None:
        for path in sorted(paths):
            self.run_for_path(path, extra)

    def run_for_path(self, path: Path, extra: Extra) -> None:
        self.run_for_folder(Folder.from_path(path), extra)

    def run_for_folder(self, folder: Folder, extra: Extra) -> None:
        photoset = Photoset.from_folder(folder)

        if photoset is None:
            print(f"Folder {folder} is no photoset.")

            return

        for migration in self.context.photoset_migrations_factory.part_less_migrations():
            migration.migrate(photoset)

            photoset.folder.refresh()

        for part in photoset.parts:
            for migration in self.context.photoset_migrations_factory.part_wise_migrations():
                migration.migrate(part)

                part.folder.refresh()

        photoset.folder.refresh()

        self.run_for_photoset(photoset, extra)

        PatternCommand.__handle_aftershoot(photoset, self.context)

    def run_for_photoset(self, photoset: Photoset, extra: Extra) -> None:
        extra |= {
            PatternCommand.SET_NAME: photoset.name,
        }

        for part in photoset.parts:
            if part.name != photoset.name:
                part_full_name = f"{photoset.name}/{part.name}"
            else:
                part_full_name = part.name

            self.run_for_part(part, extra | {
                PatternCommand.PART_FULL_NAME: part_full_name,
            })

    def run_for_part(self, part: Photoset, extra: Extra) -> None:
        assert False

    @staticmethod
    def __handle_aftershoot(photoset: Photoset, context: Context) -> None:
        """Handle aftershoot statistics."""

        root = photoset.folder
        aftershoot_folder = root["aftershoot"]

        if not aftershoot_folder:
            return

        print("__handle_aftershoot")

        af_root = context.aftershoot_stats.with_suffix("")
        af_root.mkdir(parents=True, exist_ok=True)

        af_json_path = af_root / f"{photoset.name}.json"

        if af_json_path.exists():
            with af_json_path.open() as af_json:
                af_stats = json.load(af_json)
        else:
            af_stats = {}

        local_stat = af_stats

        for subfolder in aftershoot_folder.subfolders:
            local_stat[subfolder.name] = [file.stem for file in subfolder.files]

        local_stat["good"] = [source.stem for source in photoset.sources]
        local_stat["release"] = list(set(jpeg.stem for jpeg in photoset.results))

        if PatternCommand.__validate_aftershoot(af_stats):
            with af_json_path.open("w") as af_json:
                json.dump(af_stats, af_json, indent=4)

            print("aftershoot stats successfully written.")
        else:
            print("validation failed")

    @staticmethod
    def __validate_aftershoot(stats: Dict[str, Any]) -> bool:
        """Validate aftershoot statistics."""
        marks = set()

        for i in range(5):
            i_marks = stats.get(f"{i + 1}", [])

            if not marks.isdisjoint(i_marks):
                return False

            marks.update(i_marks)

        good = stats.get("good", [])

        if not good:
            return False

        print(set(good).difference(marks))

        if not marks.issuperset(good):
            return False

        release = stats.get("release", [])

        if not release:
            return False
        if not marks.issuperset(release):
            return False
        if not set(good).issuperset(release):
            return False

        return True
