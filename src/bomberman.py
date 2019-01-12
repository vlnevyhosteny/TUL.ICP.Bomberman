import pygame
from pygame.locals import *
# from OpenGL.GL import *
# from OpenGL.GLU import *

from src.config.window_config import WindowConfig
from src.game_event_handler import *
from src.game_window import *


def main():
    pygame.init()
    pygame.display.set_mode((WindowConfig.WIDTH, WindowConfig.HEIGHT), DOUBLEBUF | OPENGL)

    window_init(WindowConfig)

    while True:
        resolver_events(pygame)
        window_clear()

        # fkin bomberman

        pygame.display.flip()
        pygame.time.wait(10)


if __name__ == '__main__':
    main()
