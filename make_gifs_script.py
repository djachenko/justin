from pathlib import Path

from v3_0.actions.stage.helpers.gif_maker import GifMaker


def main():
    maker = GifMaker()

    path = Path("I:/photos/stages/stage0.gif/19.09.21.fen_init_hell")

    maker.make_gif(path / "gif", path.name)


if __name__ == '__main__':
    main()
