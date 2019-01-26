from src.config.window_config import WindowConfig
from src.game_window import GameWindow, pyglet


def main():
    window = GameWindow(WindowConfig)
    pyglet.app.run()


if __name__ == '__main__':
    main()
