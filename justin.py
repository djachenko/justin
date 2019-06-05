import argparse

from command.command_check import CommandCheck
from v3_0.commands.command_stage import StageCommand
from v3_0.models.world import World


class Args(argparse.Namespace):
    def __init__(self, world: World) -> None:
        super().__init__()

        self.world = world


def run(args=None):
    world = World()

    commands = [
        StageCommand(),
        CommandCheck()
    ]

    parser = argparse.ArgumentParser()

    parser_adder = parser.add_subparsers()

    for command in commands:
        command.configure_parser(parser_adder)

    name = parser.parse_args(args, namespace=Args(world))

    if name.func:
        name.func(name)


if __name__ == '__main__':
    run()
