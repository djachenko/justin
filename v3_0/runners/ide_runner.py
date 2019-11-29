from pathlib import Path

from v3_0.runners import general_runner

if __name__ == '__main__':
    commands = [
        "schedule D:/photos/stages/stage2.develop/19.03.22.*",
        "publish D:/photos/stages/stage0.gif/17.06.29.nsu_holi",
        "ourate /Volumes/pestilence/photos/stages/stage2.ourate/19.11.17*",
        "upload -s 1",
        "local_sync",
        "rearrange -s 1",
        "archive D:/photos/stages/stage4.published/18.04.25.*",
        "move H:/photos/stages/stage2.develop/19.11.02.photonight",
    ]

    general_runner.run(
        Path(__file__).parent.parent.parent,
        commands[2].split()
    )
