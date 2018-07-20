import argparse
import os

from command.command_check import CommandCheck
from command.command_stage import StageCommand
from filesystem.path import Path
from models.world import World


class Args:
    def __init__(self) -> None:
        super().__init__()

        self.path = Path.from_string(os.getcwd())
        self.world = World()


def main(args=None, path=None):
    commands = [
        StageCommand(),
        CommandCheck()
    ]

    parser = argparse.ArgumentParser()

    parser_adder = parser.add_subparsers()

    for command in commands:
        command.configure_parser(parser_adder)

    name = parser.parse_args(args, namespace=Args())

    if path is not None:
        name.path = path

    if name.func:
        name.func(name)


if __name__ == '__main__':
    main()
