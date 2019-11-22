from v3_0.shared.filesystem import fs


def main():
    path = 'D:\photos\stages\stage3.ready\_piter'.replace("\\", "/")

    subfolders = fs.subfolders(path)

    for subfolder in subfolders:
        if len(subfolder.name.split_forward(".")) < 4:
            continue

        components = subfolder.name.rsplit(".", 2)

        components[2] = "piter_day" + str(int(components[1]) - 4)

        new_name = ".".join(components)

        fs.rename(subfolder, new_name)

        a = 7

if __name__ == '__main__':
    main()