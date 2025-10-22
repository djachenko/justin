from typing import Iterable

from postmypost_rest_sdk import PublicationsResponse

__PAGE_KEY = "page"
__PER_PAGE_KEY = "per_page"


def get_all(source, **kwargs) -> Iterable:
    assert __PAGE_KEY not in kwargs
    assert __PER_PAGE_KEY not in kwargs

    kwargs = kwargs.copy()

    kwargs[__PER_PAGE_KEY] = 50

    while True:
        result: PublicationsResponse = source(**kwargs)

        for element in result.data:
            yield element

        if result.pages.page != result.pages.page:
            break

        kwargs[__PAGE_KEY] = result.pages.page + 1
