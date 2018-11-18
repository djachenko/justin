import shutil

MAIN_FOLDER = "D:\photos\stages\stage2.develop\_piter"

from v3_0.filesystem import fs


def main():
    subfolders = fs.subfolders(MAIN_FOLDER)

    for subfolder in subfolders:
        if not fs.path_exists(fs.build_path(subfolder.path, "justin", "piter2017")):
            piter_folders = fs.subfolders(fs.build_path(subfolder.path, "justin"))

            for piter_folder in piter_folders:
                fs.move_down(piter_folder.path, "piter2017")

                print("moved down {0} of {1}".format(piter_folder.name, subfolder.name))
        else:
            print(subfolder.name + " is okay")

    for subfolder in subfolders:
        if fs.path_exists(fs.build_path(subfolder.path, "our_people")):
            # os.makedirs(fs.build_path(MAIN_FOLDER, "ann", subfolder.name))

            shutil.move(fs.build_path(subfolder.path, "our_people"), fs.build_path(MAIN_FOLDER, "ann", subfolder.name))

if __name__ == '__main__':
    main()