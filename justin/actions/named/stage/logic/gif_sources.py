from typing import List, Iterable

from justin_utils import joins, util

from justin.actions.named.stage.logic.base import Check, Problem
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
    def get_problems(self, photoset: Photoset) -> Iterable[Problem]:
        super_problems = super().get_problems(photoset)

        if super_problems and util.ask_for_permission("\n" + self.message):
            return []

        return super_problems
