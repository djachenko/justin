def main():
    path = "D:/photos/recovered/"

    duplicates = [l.rsplit(maxsplit=1)[0] for l in open(path + "_duplicates.txt")]
    unfound = [l.rsplit(maxsplit=1)[0] for l in open(path + "unfound.txt")]

    collisions = list(set(duplicates).intersection(unfound))

    to_check = [l for l in open(path + "_duplicates.txt") if l.rsplit(maxsplit=1)[0] not in collisions]

    a = 7


if __name__ == '__main__':
    main()


def collide():
    sets = []

    mapping = {}

    for photoset in sets:
        key = photoset.name
        bucket = mapping.get(key, [])

        bucket.append(photoset)

        mapping[key] = bucket

    buckets = mapping.values()

    collisions = [bucket for bucket in buckets if len(bucket) > 1]
