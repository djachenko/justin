from typing import Callable


class LazyProxy:
    def __init__(self, generator: Callable) -> None:
        super().__init__()

        self.__generator = generator
        self.__value = None

    def __get(self):
        if self.__generator:
            self.__value = self.__generator()
            self.__generator = None

        return self.__value

    def __getattr__(self, name):
        return getattr(self.__value, name)
