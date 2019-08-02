import os


def main():
    path = "D:/photos/stages/stage3.ready/17.04.23.mmf_median"

    jpeg_path = path + "/photoclub"

    jpeg_entries = os.scandir(jpeg_path)

    jpeg_files = [i.name for i in jpeg_entries]
    jpeg_names = set([jpeg_file.split_forward(".")[0] for jpeg_file in jpeg_files])

    sources = os.scandir(path)

    saved_dir = path + "/nefs"

    os.makedirs(saved_dir, exist_ok=True)

    count = 0

    for source in sources:
        pic_name = source.name.split_forward(".")[0]

        if source.is_file() and pic_name in jpeg_names:
            os.rename(source.path, saved_dir + "/" + source.name)

            # copyfile(source.path, saved_dir + "/" + source.name)

            count += 1

            print("copy {1} {2}/{3}".format("", source.name, count, len(jpeg_names)))


if __name__ == '__main__':
    main()
