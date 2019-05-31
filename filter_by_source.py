from v3_0.filesystem import fs

__source_folder = "D:/photos/stages/stage2.develop/_/17.08.05.lika_night_lake"
__jpeg_folder = "selection"


def joins(selector, *seqs):
    enumerated_seqs = enumerate(seqs)

    merges = {}

    for seq_num, seq in enumerated_seqs:
        for item in seq:
            key = selector(item)

            if key not in merges:
                merges[key] = {}

            merges[key][seq_num] = item

    results = []

    for merge in merges:
        merge_list = [merge.get(i, None) for i in range(len(seqs))]

        results.append(merge_list)

    return results


def join(a, b, selector):
    merges = {}

    for i in a:
        key = selector(i)

        if key not in merges:
            merges[key] = {}

        merges[key][0] = i

    for i in b:
        key = selector(i)

        if key not in merges:
            merges[key] = {}

        merges[key][1] = i

    results = []

    for merge in merges.values():
        results.append(list(merge.get(i, None) for i in range(2)))

    return results


def filter_by_sources():
    nefs = fs.files_by_extension(__source_folder, "nef")

    nef_names = [fs.stem(nef) for nef in nefs]

    zipped_nefs = list(zip(nef_names, nefs))

    jpegs = fs.subfiles(fs.build_path(__source_folder, __jpeg_folder))

    jpeg_names = [fs.stem(jpeg) for jpeg in jpegs]

    zipped_jpegs = list(zip(jpeg_names, jpegs))

    removed_nefs = [i for i in zipped_nefs if i[0] not in jpeg_names]
    removed_jpegs = [i for i in zipped_jpegs if i[0] not in nef_names]

    for name, file in removed_jpegs:
        fs.move_down(file.path, "non_passed")

    for name, file in removed_nefs:
        fs.move_down(file.path, "non_passed")


if __name__ == '__main__':
    filter_by_sources()
