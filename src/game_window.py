import math

from pyglet.gl import *

from src.config.window_config import WindowConfig
from src.map.map_json_parser import parse_map_from_folder

class GameWindow(pyglet.window.Window):

    def __init__(self, window_config, *args, **kwargs):
        super().__init__(resizable=window_config.IS_RESIZEABLE, *args, **kwargs)
        self.window_config = window_config
        self.set_minimum_size(window_config.WIDTH, window_config.HEIGHT)

        self.rotation = (0, 0)
        self.position = (0, 0, 0)

        self.maps = parse_map_from_folder('maps')
        self.selected_map = self.maps[0]
        self.selected_map.initialize()

        glClearColor(0.2, 0.3, 0.2, 1.0)
        glEnable(GL_DEPTH_TEST)

        pyglet.clock.schedule_interval(self.update, 1.0 / WindowConfig.TICKS_PER_SECOND)

    def on_draw(self):
        # Clear the current GL Window
        self.clear()

        self.set_3d()
        glColor3d(1, 1, 1)
        self.selected_map.batch.draw()
        self.set_2d()

    def on_resize(self, width, height):
        # set the Viewport
        glViewport(0, 0, width, height)

        # using Projection mode
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        aspect_ratio = width / height
        gluPerspective(35, aspect_ratio, 1, 1000)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -400)

    def update(self, dt):
        pass

    # def on_show(self):
    #     pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT | pyglet.gl.GL_DEPTH_BUFFER_BIT)
    #     pyglet.gl.glMatrixMode(pyglet.gl.GL_PROJECTION)
    #     pyglet.gl.glLoadIdentity()
    #     pyglet.gl.gluPerspective(45.0, float(self.window_config.WIDTH) / self.window_config.HEIGHT, 0.1, 360)

    # def on_text_motion(self, motion):
    #     if motion == key.UP:
    #         self.x_rotation -= INCREMENT
    #     elif motion == key.DOWN:
    #         self.x_rotation += INCREMENT
    #     elif motion == key.LEFT:
    #         self.y_rotation -= INCREMENT
    #     elif motion == key.RIGHT:
    #         self.y_rotation += INCREMENT

    def set_2d(self):
        """ Configure OpenGL to draw in 2d.
        """
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_3d(self):
        """ Configure OpenGL to draw in 3d.
        """
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        glTranslatef(-x, -y, -z)
