import argparse
from pathlib import Path

from v3_0.commands.command_factory import CommandFactory
from v3_0.shared.justin import Justin
from v3_0.shared.helpers.cd import cd


def run(working_path: Path, args=None):
    with cd(working_path):
        commands = CommandFactory.instance().commands()

        parser = argparse.ArgumentParser()

        parser_adder = parser.add_subparsers()

        for command in commands:
            command.configure_parser(parser_adder)

        name = parser.parse_args(args)

        if hasattr(name, "func") and name.func:
            justin = Justin.instance()

            name.func(name, justin)
        else:
            print("no parameters is bad")
