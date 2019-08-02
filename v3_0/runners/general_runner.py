import argparse
from pathlib import Path

from v3_0.commands.command_factory import CommandFactory
from v3_0.shared.configuration.configurator import Configurator
from v3_0.shared.helpers.cd import cd


def run(working_path: Path, args=None):
    with cd(working_path):
        commands = CommandFactory.instance().commands()

        parser = argparse.ArgumentParser()

        parser_adder = parser.add_subparsers()

        for command in commands:
            command.configure_parser(parser_adder)

        namespace = Configurator.instance().get_namespace()

        name = parser.parse_args(args, namespace=namespace)

        if hasattr(name, "func") and name.func:
            name.func(name)
        else:
            print("no parameters is bad")
