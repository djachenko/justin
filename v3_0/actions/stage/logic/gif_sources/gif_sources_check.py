from v3_0.actions.stage.logic.base.check import Check
from v3_0.shared.helpers import util
from v3_0.shared.models.photoset import Photoset


class GifSourcesCheck(Check):
    def check(self, photoset: Photoset) -> bool:
        super_result = super().check(photoset)

        if super_result:
            return super_result

        return util.ask_for_permission("\n" + self.message)
