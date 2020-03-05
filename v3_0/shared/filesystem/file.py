from v3_0.shared.filesystem.path_based import PathBased


class File(PathBased):

    @property
    def name(self):
        return self.path.name

    @property
    def size(self):
        return self.path.stat().st_size

    def is_file(self) -> bool:
        return self.path.is_file()

    def is_dir(self) -> bool:
        return self.path.is_dir()

    @property
    def mtime(self):
        return self.path.stat().st_mtime

    def stem(self) -> str:
        name = self.path.stem

        # todo: extract this from File
        if "-" in name:
            name_and_modifier = name.rsplit("-", 1)

            modifier = name_and_modifier[1]

            if modifier.isdecimal():
                name = name_and_modifier[0]

        return name

    @property
    def extension(self) -> str:
        return self.path.suffix

    def __str__(self) -> str:
        return "File {name}".format(name=self.name)

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, File):
            return False

        return o.path == self.path
