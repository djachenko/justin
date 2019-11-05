from pathlib import Path

from v3_0.runners import general_runner

if __name__ == '__main__':
    commands = [
        "schedule D:/photos/stages/stage2.develop/19.03.22.*",
        "publish D:/photos/stages/stage4.published/*",
        "upload -s 1",
        "local_sync",
        "archive D:/photos/stages/stage4.published/18.04.25.*",
        "move /Volumes/pestilence/photos/stages/stage2.ourate/16.12.02.test_set",
    ]

    general_runner.run(
        Path(__file__).parent.parent.parent,
        commands[5].split()
    )
