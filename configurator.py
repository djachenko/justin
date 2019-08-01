from pathlib import Path

from pyvko.pyvko import Pyvko

from config import Config
from v3_0.args import Args
from v3_0.shared.models.world import World
from v3_0.shared.singleton import Singleton


class Configurator(Singleton):
    __CONFIG_PATH = "configs/config.json"

    # noinspection PyMethodMayBeStatic
    def get_args(self) -> Args:
        config = Config.read(Path(Configurator.__CONFIG_PATH))

        pyvko = Pyvko(config.pyvko_config_path)

        group = pyvko.get_group(config.group_url)
        photos_uploader = pyvko.get_photos_uploader()

        world = World()

        args = Args(world=world, group=group, uploader=photos_uploader)

        return args
