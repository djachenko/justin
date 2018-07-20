import os


def compare(path_from, path_to):
    contents = os.scandir(path_from)

    # print(path_from, path_to)

    # a = [content.name for content in contents]

    for entry in contents:
        if not os.path.exists(path_to + "/" + entry.name):
            print("-", path_to + "/" + entry.name)
        elif entry.is_dir():
            compare(entry.path, path_to + "/" + entry.name)


def main():
    path_from = "D:/"
    path_to = "H:/"

    way = "photos/albums"

    compare(path_from + way, path_to + way)


if __name__ == '__main__':
    main()
