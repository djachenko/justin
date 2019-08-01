#! venv/Scripts/python
# https://stackoverflow.com/questions/1934675/how-to-execute-python-scripts-in-windows - in case running will break

import argparse
from pathlib import Path

from configurator import Configurator
from v3_0.commands.command_factory import CommandFactory
from v3_0.shared.helpers.cd import cd


def run(args=None):
    commands = CommandFactory.instance().commands()

    parser = argparse.ArgumentParser()

    parser_adder = parser.add_subparsers()

    for command in commands:
        command.configure_parser(parser_adder)

    namespace = Configurator.instance().get_args()

    name = parser.parse_args(args, namespace=namespace)

    if hasattr(name, "func") and name.func:
        name.func(name)


if __name__ == '__main__':
    with cd(Path(__file__).parent):
        run()
