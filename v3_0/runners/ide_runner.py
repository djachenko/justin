from pathlib import Path

from v3_0.runners import general_runner

if __name__ == '__main__':
    stage_commands = [
        "develop",             # 0
        "ourate",              # 1
        "ready",               # 2
        "publish",             # 3
        "archive",             # 4
        "move",                # 5
        "make_gif",            # 6
        "split",               # 7
        "fix_metafile",        # 8
        "resize_gif_sources",  # 9
    ]

    locations = [
        "D:/",                   # 0
        "H:/",                   # 1
        "/Volumes/pestilence/",  # 2
    ]

    stages = [
        "stage0.gif",        # 0
        "stage2.develop",    # 1
        "stage2.ourate",     # 2
        "stage3.ready",      # 3
        "stage4.published",  # 4
    ]


    def build_command(command, location, stage, name):
        return f"{stage_commands[command]} {locations[location]}photos/stages/{stages[stage]}/{name}"


    commands = [
        build_command(9, 1, 0, "20*"),
        "upload -s 1",
        "local_sync",
        "rearrange -s 1",
        "delay"
    ]

    general_runner.run(
        Path(__file__).parent.parent.parent,
        commands[0].split()
    )
