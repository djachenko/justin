import os

import util

__copies_folder = "copies"


def undo_filter_copies(path):
    copies = os.scandir(path + "/" + __copies_folder)

    for copy in copies:
        os.rename(copy.path, path + "/" + copy.name)

    os.removedirs(path + "/" + __copies_folder)


def filter_copies(path):
    entries = os.scandir(path)

    jpegs = [entry for entry in entries if entry.name.lower().endswith(".jpg")]
    raws = [entry for entry in entries if entry not in jpegs]

    jpeg_names = util.names_without_extension([entry.name for entry in jpegs])
    raw_names = util.names_without_extension([entry.name for entry in raws])

    copies_names = set(jpeg_names).intersection(raw_names)

    if len(copies_names) > 0:
        copies_directory = path + "/" + __copies_folder

        os.makedirs(copies_directory)

        for jpeg in jpegs:
            if util.name_without_extension(jpeg.name) in copies_names:
                os.rename(jpeg.path, copies_directory + "/" + jpeg.name)
