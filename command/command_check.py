from command.command import Command


class CommandCheck(Command):
    def run(self, args):
        super().run(args)

        world = args.world

        disks_valid = all([disk.check_structure() for disk in world.disks])

        # if disks_valid:
        for disk in world.disks:
            for photoset in disk.photosets:
                photoset.check_structure()

    def configure_parser(self, parser_adder):
        super().configure_parser(parser_adder)

        subparser = parser_adder.add_parser("check")

        self.setup_callback(subparser)
