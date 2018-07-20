import os


class MockDirEntry:
    # no doc
    def inode(self):  # real signature unknown
        return self.__stats[False].st_ino

    def is_dir(self, follow_symlinks=True):  # real signature unknown
        return os.path.isdir(self.path)

    def is_file(self, follow_symlinks=True):  # real signature unknown
        return os.path.isfile(self.path)

    def is_symlink(self):  # real signature unknown
        return os.path.islink(self.path)

    def stat(self, follow_symlinks=True):  # real signature unknown
        return self.__stats[follow_symlinks]

    def __fspath__(self, follow_symlinks=True):  # real signature unknown
        return self.path

    def __init__(self, path: str):  # real signature unknown
        super().__init__()

        self.path = path

        path = path.strip().strip("/")

        self.name = path.rsplit("/", 1)[-1]

        self.__stats = {
            True: os.stat(path, follow_symlinks=True),
            False: os.stat(path, follow_symlinks=False)
        }