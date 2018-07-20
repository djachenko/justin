import os


def undo_split_by_extension(path):
    for directory in [i for i in os.scandir(path) if i.is_dir()]:
        entries = os.scandir(directory.path)

        for entry in entries:
            os.rename(entry.path, path + "/" + entry.name)

        os.removedirs(directory)


def split_by_extension(path):
    entries = os.scandir(path)

    for entry in [i for i in entries if i.is_file()]:
        entry_name = entry.name

        extension = entry_name.split_forward(".")[-1] + "s"
        extension = extension.lower()

        filetype_dir = path + "/" + extension

        os.makedirs(filetype_dir, exist_ok=True)

        os.rename(entry.path, filetype_dir + "/" + entry_name)


def run(path):
    files = [entry for entry in os.scandir(path) if entry.is_file()]

    if len(files) > 0:
        split_by_extension(path)
    else:
        undo_split_by_extension(path)
