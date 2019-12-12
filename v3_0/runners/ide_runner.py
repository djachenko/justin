from pathlib import Path

from v3_0.runners import general_runner

if __name__ == '__main__':
    stage_commands = [
        "develop",
        "ourate",
        "ready",
        "publish",
        "archive",
        "move",
    ]

    locations = [
        "D:/",
        "H:/",
        "/Volumes/pestilence/"
    ]

    stages = [
        "stage0.gif",
        "stage2.develop",
        "stage2.ourate",
        "stage4.published",
    ]

    def build_command(command, location, stage, name):
        return f"{stage_commands[command]} {locations[location]}photos/stages/{stages[stage]}/{name}"


    commands = [
        build_command(2, 1, 2, "19.10.11**"),
        "upload -s 1",
        "local_sync",
        "rearrange -s 1",
    ]

    general_runner.run(
        Path(__file__).parent.parent.parent,
        commands[0].split()
    )
