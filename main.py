import justin
from pathlib import Path


def test_stage():
    x = 1

    set_names = [
        # "17.12.25.smola_opening",
        "18.06.12.forro_na_siberia",
    ]

    for set_name in set_names:
        if x == 1:
            justin.main([
                "ourate",
                set_name,
            ],
                Path.from_string("D:/photos/stages/stage2.develop"))
        else:
            justin.main([
                "develop",
                set_name,
            ],
                Path.from_string("D:/photos/stages/stage2.ourate"))


if __name__ == '__main__':
    test_stage()

    a = 7
