import argparse

from v3_0.commands.command_factory import CommandFactory
from v3_0.models.world import World


class Args(argparse.Namespace):
    def __init__(self, world: World) -> None:
        super().__init__()

        self.world = world


def run(args=None):
    world = World()

    commands = CommandFactory.instance().commands()

    parser = argparse.ArgumentParser()

    parser_adder = parser.add_subparsers()

    for command in commands:
        command.configure_parser(parser_adder)

    name = parser.parse_args(args, namespace=Args(world))

    if name.func:
        name.func(name)


if __name__ == '__main__':
    run()
