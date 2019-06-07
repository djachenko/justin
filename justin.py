#! venv/Scripts/python
# https://stackoverflow.com/questions/1934675/how-to-execute-python-scripts-in-windows - in case running will break

import argparse
import sys

from v3_0.commands.command_factory import CommandFactory
from v3_0.models.world import World


class Args(argparse.Namespace):
    def __init__(self, world: World) -> None:
        super().__init__()

        self.world = world


def run(args):
    world = World()

    commands = CommandFactory.instance().commands()

    parser = argparse.ArgumentParser()

    parser_adder = parser.add_subparsers()

    for command in commands:
        command.configure_parser(parser_adder)

    if len(args) < 2:
        parser.error("Please choose the command")

    name = parser.parse_args(args, namespace=Args(world))

    if hasattr(name, "func") and name.func:
        name.func(name)


if __name__ == '__main__':
    run(sys.argv)
