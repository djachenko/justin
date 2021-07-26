from pathlib import Path


def main():

    paths = [
        Path("c:/users/justin/photos/stages/stage2.develop/21.05.29.fj_median/timelapse/frames/camera_5"),
    ]

    for path in paths:
        files = list(path.iterdir())

        files.sort(key=lambda x: x.name)

        for index, file in enumerate(files):
            file.rename(file.parent / f"{index:04}{file.suffix}")


if __name__ == '__main__':
    main()
