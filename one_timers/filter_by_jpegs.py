from v3_0.helpers import util
from pathlib import Path
from v3_0.models.photoset import Photoset
from models.world import World


def main():
    world = World()

    basketball: Photoset = world.element_by_path(Path.from_string('D:\photos\stages\stage0.gif\\17.10.23.basketball'))

    files = basketball.entry.subfiles()

    jpegs = [file for file in files if file.extension == "jpg"]
    nefs = [file for file in files if file.extension == "nef"]

    join = util.left_join(
        nefs,
        jpegs,
        lambda x: x.stem()
    )

    non_paired = [nef for nef, jpeg in join if jpeg is None]

    for nef in non_paired:
        nef.move_down("non_passed")

    a = 7


if __name__ == '__main__':
    main()
