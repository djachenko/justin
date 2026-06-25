from justin.shared.filesystem import File, RelativeFileset
from justin.shared.metafiles.metafile import RootMetafile
from justin.shared.models.photoset import Photoset
from justin.typer.stage_command.abstracts.hook import Hook


class ProgressHook(Hook):
    """
    Хук для стейджа develop.
    fix — no-op (намеренно пусто).
    unfix — возвращает файлы из progress обратно.
    """

    @property
    def name(self) -> str:
        return "progress hook"

    def unfix(self, photoset: Photoset) -> None:
        filtered = photoset.folder["progress"]

        if not filtered:
            return

        metafiles = [
            File(path)
            for path in RootMetafile.collect_metafile_paths(filtered)
            if path.exists()
        ]

        RelativeFileset(filtered.path, filtered.flatten() + metafiles).move_up()

        photoset.folder.refresh()
