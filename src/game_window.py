from pyglet.gl import *
from pyglet.window import key
from OpenGL.GLUT import *

INCREMENT = 5

class GameWindow(pyglet.window.Window):

    x_rotation = y_rotation = 30

    def __init__(self, window_config, *args, **kwargs):
        super().__init__(resizable=window_config.IS_RESIZEABLE, *args, **kwargs)
        self.window_config = window_config
        self.set_minimum_size(window_config.WIDTH, window_config.HEIGHT)

        glClearColor(0.2, 0.3, 0.2, 1.0)
        glEnable(GL_DEPTH_TEST)

    def on_draw(self):
        # Clear the current GL Window
        self.clear()

        # Push Matrix onto stack
        glPushMatrix()

        glRotatef(self.x_rotation, 1, 0, 0)
        glRotatef(self.y_rotation, 0, 1, 0)

        # Draw the six sides of the cube
        glBegin(GL_QUADS)

        glColor4f(1.0, 0, 0, 1.0)

        # White
        glColor3ub(255, 255, 255)
        glVertex3f(50, 50, 50)

        # Yellow
        glColor3ub(255, 255, 0)
        glVertex3f(50, -50, 50)

        # Red
        glColor3ub(255, 0, 0)
        glVertex3f(-50, -50, 50)
        glVertex3f(-50, 50, 50)

        # Blue
        glColor3f(0, 0, 1)
        glVertex3f(-50, 50, -50)

        #

        glEnd()

        # Pop Matrix off stack
        glPopMatrix()

    def on_resize(self, width, height):
        # set the Viewport
        glViewport(0, 0, width, height)

        # using Projection mode
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        aspectRatio = width / height
        gluPerspective(35, aspectRatio, 1, 1000)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -400)

    # def on_show(self):
    #     pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT | pyglet.gl.GL_DEPTH_BUFFER_BIT)
    #     pyglet.gl.glMatrixMode(pyglet.gl.GL_PROJECTION)
    #     pyglet.gl.glLoadIdentity()
    #     pyglet.gl.gluPerspective(45.0, float(self.window_config.WIDTH) / self.window_config.HEIGHT, 0.1, 360)

    def on_text_motion(self, motion):
        if motion == key.UP:
            self.x_rotation -= INCREMENT
        elif motion == key.DOWN:
            self.x_rotation += INCREMENT
        elif motion == key.LEFT:
            self.y_rotation -= INCREMENT
        elif motion == key.RIGHT:
            self.y_rotation += INCREMENT
