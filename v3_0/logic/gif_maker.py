from pathlib import Path
from typing import List

from PIL import Image

from v3_0.models.photoset import Photoset


class GifMaker:
    __START_MIN_SIZE = 0
    __START_MAX_SIZE = 1500

    __MB = 1024 * 1024

    __MAX_DESIRED_SIZE = 200 * __MB
    __MIN_DESIRED_SIZE = 199 * __MB

    @staticmethod
    def __make_gif(sources: Path, name: str, size: int):
        frames_paths = [i for i in sources.iterdir() if i.suffix == ".jpg"]

        frames: List[Image] = []

        for index, frame_path in enumerate(frames_paths):
            frame = Image.open(frame_path)

            frame.thumbnail((size, size), Image.ANTIALIAS)

            frames.append(frame)

        frames[0].save(
            sources / name,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=10,
            loop=0
        )

    @staticmethod
    def __gif_has_good_size(gif_path: Path) -> bool:
        gif_size = gif_path.stat().st_size

        return GifMaker.__MIN_DESIRED_SIZE < gif_size < GifMaker.__MAX_DESIRED_SIZE

    def make(self, photoset: Photoset):
        if photoset.gif is None:
            return

        sources_path = photoset.gif.path
        gif_name = f"{photoset.name}.gif"

        gif_path = sources_path / gif_name

        if gif_path.exists() and self.__gif_has_good_size(gif_path):
            print("Valid gif already exists")

            return

        min_size = GifMaker.__START_MIN_SIZE
        max_size = GifMaker.__START_MAX_SIZE

        while True:
            iteration_size = (min_size + max_size) // 2

            print(f"Starting iteration with size {iteration_size}")

            self.__make_gif(sources_path, gif_name, iteration_size)

            gif_size = gif_path.stat().st_size

            gif_size_in_mb = round(gif_size / GifMaker.__MB, 2)

            if GifMaker.__MIN_DESIRED_SIZE < gif_size < GifMaker.__MAX_DESIRED_SIZE:
                print(f"Iteration {iteration_size} successful, final result lies at {gif_path.name}")

                break
            elif gif_size > GifMaker.__MAX_DESIRED_SIZE:
                print(f"GIF too large ({gif_size_in_mb} MB), decreasing")

                max_size = iteration_size
            else:
                print(f"GIF too small ({gif_size_in_mb} MB), increasing")

                min_size = iteration_size
