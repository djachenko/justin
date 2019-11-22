import os


def main():
    path = "D:/photos/recovered/"
    source_filename = "deleted_files.txt"

    name_key = "name"
    path_key = "path"

    files = []

    with open(path + source_filename, encoding="utf-8") as file:
        for s in file:
            s_arr = s.rsplit(maxsplit=2)

            s_dict = {
                name_key: s_arr[0],
                path_key: s_arr[2].strip("\\").split("\\")[2:]
            }

            files.append(s_dict)

    filenames = [file[name_key] for file in files]

    stats = {}

    for name in filenames:
        if name not in stats:
            stats[name] = 0

        stats[name] += 1

    nonuniques = [stat for stat in stats if stats[stat] > 1]

    nonuniques_with_paths = {}

    for file in files:
        filename = file[name_key]
        if filename in nonuniques:
            if filename not in nonuniques_with_paths:
                nonuniques_with_paths[filename] = []

            nonuniques_with_paths[filename].append("/".join(file[path_key]))

    with open(path + "_duplicates.txt", "w") as duplicates:
        for nonunique_name, nonunique_paths in nonuniques_with_paths.items():
            for p in nonunique_paths:
                duplicates.write(nonunique_name + "\t\t\t" + p + "\n")

    for i in files:
        filename = i[name_key]
        filepath = i[path_key]

        absolute_path = path

        for level in filepath:
            absolute_path += level + "/"

            if not os.path.exists(absolute_path):
                os.makedirs(absolute_path)
            elif not os.path.isdir(absolute_path):
                print("there was file: ", absolute_path)

                break
        new_path = path + "/".join(filepath) + "/"

        if os.path.exists(path + filename):
            os.rename(path + filename, new_path + filename)
        else:
            with open(path + "unfound.txt", "a") as copies:
                copies.write(filename + "\t" + new_path + "\n")

    a = 7


if __name__ == '__main__':
    main()
