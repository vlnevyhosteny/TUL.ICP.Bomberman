from src.config.window_config import WindowConfig
from src.game_window import GameWindow, pyglet


def main():
    window = GameWindow(WindowConfig)
    #pyglet.clock.schedule_interval(window.update, 1/30.0)
    pyglet.app.run()


if __name__ == '__main__':
    main()
