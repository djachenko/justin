import json
from pathlib import Path


def main():
    root = Path().absolute().parent.parent / ".justin"

    with (root / "my_people.json").open() as my_people_file:
        my_people = json.load(my_people_file)

    with (root / "closed.json").open() as closed_file:
        closed = json.load(closed_file)

    merged_dict = {}

    for person in closed + my_people:
        if person["vk_id"] == 0:
            person["vk_id"] = None

        merged_dict[person["folder"]] = person

    merged_list = list(merged_dict.values())

    merged_list = sorted(merged_list, key=lambda x: x["register_date"])

    with (root / "cms" / "migrated.json").open("w") as migrated_json:
        json.dump({
            "entries": merged_list
        }, migrated_json, indent=4, ensure_ascii=False)

    a = 7


if __name__ == '__main__':
    main()
