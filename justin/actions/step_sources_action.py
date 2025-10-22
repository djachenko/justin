from argparse import Namespace
from datetime import timedelta
from math import floor

from justin.actions.pattern_action import PatternAction, Extra
from justin.shared.context import Context
from justin.shared.models.photoset import Photoset


class StepSourcesAction(PatternAction):
    def perform_for_photoset(self, photoset: Photoset, args: Namespace, context: Context, extra: Extra) -> None:
        if not photoset.sources:
            return

        sorted_sources = sorted(photoset.sources, key=lambda s: s.exif.date_taken)

        first_source_timestamp = sorted_sources[0].exif.date_taken

        minute_start = floor(first_source_timestamp.minute / 15) * 15

        bucket_size = timedelta(minutes=15)
        bucket_end = first_source_timestamp.replace(minute=minute_start, second=0)
        bucket_count = 0
        bucket_name = ""

        for source in sorted_sources:
            while source.exif.date_taken >= bucket_end:
                bucket_start = bucket_end
                bucket_end = bucket_start + bucket_size

                bucket_count += 1
                bucket_name = f"{bucket_count:02}.{bucket_start.hour:02}{bucket_start.minute:02}"

                bucket_path = photoset.folder / bucket_name
                bucket_path.mkdir()

            source.move_down(bucket_name)


