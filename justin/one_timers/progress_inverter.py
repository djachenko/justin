from pathlib import Path

from justin.shared.filesystem import Folder


def main():
    root = Folder.from_path(Path("/Users/justin/photos/stages/stage2.develop/25.04.01.kbrd_cabbager"))

    progress_folder = root / "progress"
    progress_folder.mkdir()

    for subfolder in root.subfolders:
        progress = subfolder / "progress"

        if not progress.exists():
            continue

        progress.rename(subfolder.name)
        progress.move(progress_folder.path)


if __name__ == '__main__':
    main()
