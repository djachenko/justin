from lazy_object_proxy import Proxy as _Proxy


class Proxy(_Proxy):
    def __next__(self):
        return next(self.__wrapped__)
