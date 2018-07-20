def func1():
    piter_path = __develop + "_piter/"
    piter_folders = [folder for folder in fs.subfolders(piter_path) if "piter_day" in folder.name]

    piter_tree = fs.folder_tree(piter_path + "sources/", 1)
    results_tree = fs.folder_tree(piter_path + "justin/", 1)

    del results_tree["undated"]

    for i in results_tree:
        for j in piter_tree:
            sources_names = set([key.rsplit(".", 1)[0] for key in piter_tree[j].keys()])
            results_names = set([key.rsplit(".", 1)[0] for key in results_tree[i].keys()])

            common = sources_names.intersection(results_names)

            if len(common) > 0:
                dest_path = fs.build_path(piter_path, "sources", j, "justin", i)

                print(dest_path)

                for name in common:
                    fs.move_file(results_tree[i][name + ".jpg"], dest_path)


def func2():
    piter_path = __develop + "_piter/sources"

    folders = fs.subfolders(piter_path)

    for folder in folders:
        signed = fs.all_files(fs.build_path(folder.path, "justin"))
        unsigned = fs.all_files(fs.build_path(folder.path, "selection"))

        signed_names = [i.name for i in signed]

        odd = [i for i in unsigned if i.name not in signed_names]

        if len(odd) > 0:
            dest_dir = fs.build_path(folder.path, "selection", "odd")

            print(dest_dir)

            for i in odd:
                fs.move_down(i, "odd")