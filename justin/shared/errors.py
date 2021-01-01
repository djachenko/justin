class JustinError(Exception):
    def __init__(self, message: str) -> None:
        self.__message = message

    @property
    def message(self):
        return self.__message
