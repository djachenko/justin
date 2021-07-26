from datetime import datetime
from pathlib import Path

from pyvko.config.config import Config
from pyvko.pyvko_main import Pyvko


def main():
    pyvko = Pyvko(Config({
        "token": "2f6795fd1ee279c4f3f15fe8a3b291420b31d07c6b48985b3d5c57194135597f253d66bd223898d210f6f"
    }))

    group = pyvko.get("djachenko")

    root = Path("C:/Users/justin/photos/stages/stage2.develop/21.04.24.ggf_init")

    for part in ["1", "2"]:
        photos = root / part / "progress/justin/"

        album = group.create_album(f"{root.name}_{part}")

        start = datetime.now()
        skip_count = 0

        for index, file in enumerate(photos.iterdir(), start=1):
            if index <= skip_count:
                continue

            if file.is_file():
                album.add_photo(file)

                now = datetime.now()
                delta = now - start

                print(f"Uploaded {index} file {file.name} in {album.name} ({now}, {delta}, {delta / index})")


if __name__ == '__main__x':
    main()
