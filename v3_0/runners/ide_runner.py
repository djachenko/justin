from pathlib import Path

from v3_0.runners import general_runner

if __name__ == '__main__':
    general_runner.run(
        Path(__file__).parent.parent.parent,
        # "schedule 17.06.12.nsu_hull".split()
        "upload".split()
    )
