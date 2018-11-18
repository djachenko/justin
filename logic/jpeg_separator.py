from v3_0.filesystem import fs

__SEPARE = "separated_jpegs"


class JpegSeparator:
    def __forward(self):
        jpegs = fs.files_by_extension(self.path, "jpg")

        for jpeg in jpegs:
            jpeg.move_down(__SEPARE)

    def __backwards(self):
        separated = fs.subfiles(fs.build_path(self.path, __SEPARE))

        for file in separated:
            file.move_up()

        fs.remove_tree(fs.build_path(self.path, __SEPARE))

    def separate_files(self):
        if fs.path_exists(fs.build_path(self.path, __SEPARE)):
            self.__backwards()
        else:
            self.__forward()
