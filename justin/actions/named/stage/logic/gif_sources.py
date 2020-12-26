from typing import List

from justin_utils import joins, util

from justin.actions.named.stage.logic.base import Check
from justin.actions.named.stage.logic.base import Selector
from justin.shared.models.photoset import Photoset


class GifSourcesSelector(Selector):
    def select(self, photoset: Photoset) -> List[str]:
        if photoset.gif is None:
            return []

        gif_sources = photoset.gif.flatten()
        sources = photoset.sources

        join = joins.right(
            gif_sources,
            sources,
            lambda gif, source: gif.stem() == source.stem()
        )

        nongifed_sources_names = [source.stem() for gif, source in join if gif is None]

        return nongifed_sources_names


class GifSourcesCheck(Check):
    def is_good(self, photoset: Photoset) -> bool:
        super_result = super().is_good(photoset)

        if super_result:
            return super_result

        return util.ask_for_permission("\n" + self.message)
