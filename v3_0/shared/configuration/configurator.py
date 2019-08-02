from pathlib import Path

from pyvko.pyvko import Pyvko

from v3_0.args import Args
from v3_0.shared.configuration.config import Config
from v3_0.shared.models.world import World
from v3_0.shared.singleton import Singleton


class Configurator(Singleton):
    __CONFIGS_FOLDER = Path(".justin_configs")
    __CONFIG_FILE = "config.json"

    # noinspection PyMethodMayBeStatic
    def get_namespace(self) -> Args:
        config = Config.read(Path(Configurator.__CONFIGS_FOLDER / Configurator.__CONFIG_FILE))

        pyvko = Pyvko(Configurator.__CONFIGS_FOLDER / config.pyvko_config)

        group = pyvko.get_group(config.group_url)
        photos_uploader = pyvko.get_photos_uploader()

        world = World()

        args = Args(world=world, group=group, uploader=photos_uploader)

        return args
