import json
from abc import ABC
from argparse import Namespace
from pathlib import Path
from typing import List, Dict, Any

from frozendict import frozendict

from justin.shared.context import Context
from justin.shared.filesystem import Folder
from justin.shared.models.photoset import Photoset
from justin_utils import util
from justin_utils.cli import Parameter, Action

Extra = Dict[str, Any]


class PatternAction(Action, ABC):
    SET_NAME = "set_name"
    PART_FULL_NAME = "part_full_name"

    @property
    def parameters(self) -> List[Parameter]:
        return super().parameters + [
            Parameter("pattern", nargs="*", default=[Path.cwd().as_posix()])
        ]

    def perform(self, args: Namespace, context: Context) -> None:
        pattern: List[str] = args.pattern

        paths = sorted(list(util.resolve_patterns(*pattern)))

        if not any(paths):
            print("No items found for that pattern.")

            return

        extra = self.get_extra(context)

        self.perform_for_pattern(paths, args, context, extra)

    def get_extra(self, context: Context) -> Extra:
        return frozendict()

    def perform_for_pattern(self, paths: List[Path], args: Namespace, context: Context, extra: Extra) -> None:
        for path in paths:
            self.perform_for_path(path, args, context, extra)

    def perform_for_path(self, path: Path, args: Namespace, context: Context, extra: Extra) -> None:
        self.perform_for_folder(Folder.from_path(path), args, context, extra)

    def perform_for_folder(self, folder: Folder, args: Namespace, context: Context, extra: Extra) -> None:
        photoset = Photoset.from_folder(folder)

        if photoset is None:
            print(f"Folder {folder} is no photoset.")

            return

        for migration in context.photoset_migrations_factory.part_less_migrations():
            migration.migrate(photoset)

            photoset.folder.refresh()

        for part in photoset.parts:
            for migration in context.photoset_migrations_factory.part_wise_migrations():
                migration.migrate(part)

                part.folder.refresh()

        photoset.folder.refresh()

        self.perform_for_photoset(photoset, args, context, extra)

        PatternAction.__handle_aftershoot(photoset, context)

    @staticmethod
    def __handle_aftershoot(photoset: Photoset, context: Context) -> None:
        print("__handle_aftershoot")

        root = photoset.folder
        aftershoot_folder = root["aftershoot"]

        if not aftershoot_folder:
            return

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

        # af_stats[root.name] = local_stat

        if PatternAction.__validate_aftershoot(af_stats):
            with af_json_path.open("w") as af_json:
                json.dump(af_stats, af_json, indent=4)

            print("aftershoot stats successfully written.")
        else:
            print("validation failed")

    @staticmethod
    def __validate_aftershoot(stats: Dict[str, List[str]]) -> bool:
        marks = set()

        for i in range(5):
            i_marks = stats.get(f"{i + 1}", [])

            if not marks.isdisjoint(i_marks):
                return False

            marks.update(i_marks)

        good = stats["good"]

        if not good:
            return False

        print(set(good).difference(marks))

        if not marks.issuperset(good):
            return False

        release = stats["release"]

        if not release:
            return False
        if not marks.issuperset(release):
            return False
        if not set(good).issuperset(release):
            return False

        return True

    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        extra |= {
            PatternAction.SET_NAME: photoset.name,
        }

        for part in photoset.parts:
            if part.name != photoset.name:
                part_full_name = f"{photoset.name}/{part.name}"
            else:
                part_full_name = part.name

            self.perform_for_part(part, args, context, extra | {
                PatternAction.PART_FULL_NAME: part_full_name,
            })

    def perform_for_part(self, part: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        assert False
