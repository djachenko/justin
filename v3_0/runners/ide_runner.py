from pathlib import Path

from v3_0.runners import general_runner

if __name__ == '__main__':
    commands = [
        "schedule D:/photos/stages/stage2.develop/19.03.22.*",
        "upload -s 1",
        "local_sync",
    ]

    general_runner.run(
        Path(__file__).parent.parent.parent,
        commands[2].split()
    )
