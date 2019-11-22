from pathlib import Path

from v3_0.runners import general_runner


def run():
    general_runner.run(Path.home())
