from OpenGL.GL import *
from OpenGL.GLU import *


def window_init(window_config):
    gluPerspective(45, (window_config.WIDTH / window_config.HEIGHT), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)


def window_clear():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
