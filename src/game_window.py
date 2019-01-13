from pyglet.gl import *


class GameWindow(pyglet.window.Window):
    def __init__(self, window_config, *args, **kwargs):
        super().__init__(resizable=window_config.IS_RESIZEABLE, *args, **kwargs)
        self.window_config = window_config

        self.set_minimum_size(window_config.WIDTH, window_config.HEIGHT)

        glClearColor(0.2, 0.3, 0.2, 1.0)
        glEnable(GL_DEPTH_TEST)

    def on_draw(self):
        # Move the camera back a little.
        # TODO(sam): When you want to start rotating the camera, this should move into on_draw,
        # and there should be a call to gRotatef.
        pyglet.gl.glMatrixMode(pyglet.gl.GL_MODELVIEW)
        pyglet.gl.glLoadIdentity()
        pyglet.gl.glTranslatef(0, 0, -6)
        pyglet.gl.glRotatef(0, 0, 0, 0)  # seems to rotate c degrees around a point x,y,z???

        self.clear()

        pyglet.gl.glColor4f(1.0, 0, 0, 1.0)

        pyglet.graphics.draw_indexed(8, pyglet.gl.GL_LINES, [0, 1, 1, 2, 2, 3, 3, 0,  # front square
                                                             4, 5, 5, 6, 6, 7, 7, 4,  # back square
                                                             0, 4, 1, 5, 2, 6, 3, 7],  # connectors
                                     ('v3f', (-1, -1, 0,
                                              1, -1, 0,
                                              1, 1, 0,
                                              -1, 1, 0,
                                              -1, -1, -1,
                                              1, -1, -1,
                                              1, 1, -1,
                                              -1, 1, -1)))

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)

    def on_show(self):
        pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT | pyglet.gl.GL_DEPTH_BUFFER_BIT)
        pyglet.gl.glMatrixMode(pyglet.gl.GL_PROJECTION)
        pyglet.gl.glLoadIdentity()
        pyglet.gl.gluPerspective(45.0, float(self.window_config.WIDTH) / self.window_config.HEIGHT, 0.1, 360)

