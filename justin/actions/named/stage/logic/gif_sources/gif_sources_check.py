from justin_utils import util

from justin.actions.named.stage.logic.base.check import Check

from justin.shared.models.photoset import Photoset


class GifSourcesCheck(Check):
    def is_good(self, photoset: Photoset) -> bool:
        super_result = super().is_good(photoset)

        if super_result:
            return super_result

        return util.ask_for_permission("\n" + self.message)
