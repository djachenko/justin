from pathlib import Path
from typing import List, Tuple

from PIL import Image


class GifMaker:
    __START_MIN_SIZE = 0
    __START_MAX_SIZE = 1500

    __MB = 1024 * 1024

    __MAX_DESIRED_SIZE = 200 * __MB
    __MIN_DESIRED_SIZE = 195 * __MB

    @staticmethod
    def __thumbnail(path: Path, size: int) -> Image:
        frame = Image.open(path)

        frame.thumbnail((size, size), Image.LANCZOS)

        return frame

    @staticmethod
    def __make_gif(sources: Path, name: str, size: int):

        frames: List[Image] = []

        for frame_path in sources.iterdir():
            if frame_path.suffix != ".jpg":
                continue

            frame = GifMaker.__thumbnail(frame_path, size)

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
    def __sources_size(sources_path: Path) -> Tuple[int, int]:
        gif_sources_paths = filter(lambda x: x.suffix.lower() == ".jpg", sources_path.iterdir())

        first_image = Image.open(next(gif_sources_paths))

        width, height = first_image.size

        return width, height

    @staticmethod
    def __long_side(sources_path: Path) -> int:
        width, height = GifMaker.__sources_size(sources_path)

        return max(width, height)

    @staticmethod
    def __gif_has_good_size(gif_path: Path) -> bool:
        gif_size = gif_path.stat().st_size

        return GifMaker.__MIN_DESIRED_SIZE < gif_size < GifMaker.__MAX_DESIRED_SIZE

    # noinspection PyMethodMayBeStatic
    def resize_sources(self, sources: Path, scale_factor: float = 0.5):
        assert sources.is_dir()

        current_size = GifMaker.__long_side(sources)
        new_size = int(current_size * scale_factor)

        resized_name = f"resized_{new_size}"
        resized_path: Path = sources.with_name(resized_name)

        resized_path.mkdir(parents=True, exist_ok=True)

        for index, frame_path in enumerate(sources.iterdir()):
            if frame_path.suffix != ".jpg":
                continue

            frame = GifMaker.__thumbnail(frame_path, new_size)

            frame.save(resized_path / frame_path.name, "JPEG")

        sources.rename(sources.with_name(f"{sources.name}_{current_size}"))
        resized_path.rename(sources)

    # noinspection PyMethodMayBeStatic
    def make_gif(self, sources_path: Path, name: str):
        if not name.endswith(".gif"):
            name = name + ".gif"

        gif_path = sources_path / name

        if gif_path.exists() and GifMaker.__gif_has_good_size(gif_path):
            print("Valid gif already exists")

            return

        min_size = GifMaker.__START_MIN_SIZE
        max_size = min(GifMaker.__START_MAX_SIZE, GifMaker.__long_side(sources_path))

        while True:
            iteration_size = round((min_size + max_size) / 2)

            print(f"Starting iteration with size {iteration_size}... ", end="")

            GifMaker.__make_gif(sources_path, name, iteration_size)

            gif_size = gif_path.stat().st_size

            gif_size_in_mb = round(gif_size / GifMaker.__MB, 2)

            if GifMaker.__MIN_DESIRED_SIZE < gif_size < GifMaker.__MAX_DESIRED_SIZE or \
                    iteration_size == GifMaker.__START_MAX_SIZE:
                print(f"successful\nFinal result lies at {gif_path.name}")
                print(f"Scale rate: {GifMaker.__long_side(sources_path) / iteration_size:.2f}")

                break
            elif gif_size > GifMaker.__MAX_DESIRED_SIZE:
                print(f"too large ({gif_size_in_mb} MB), decreasing")

                max_size = iteration_size
            else:
                print(f"too small ({gif_size_in_mb} MB), increasing")

                min_size = iteration_size
