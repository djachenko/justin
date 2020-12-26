from pathlib import Path

from justin.runners import general_runner


def run():
    general_runner.run(Path.home())
