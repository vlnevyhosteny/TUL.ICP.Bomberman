from pyglet.gl import *
from cube import Cube


class MyWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_minimum_size(400, 300)
        glClearColor(0.2, 0.3, 0.2, 1.0)
        glEnable(GL_DEPTH_TEST)

        self.cube = Cube()

    def on_draw(self):
        self.clear()
        #glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glDrawElements(GL_TRIANGLES, len(self.cube.indices), GL_UNSIGNED_INT, None)

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)

    def update(self, dt):
        self.cube.rotate()


if __name__ == "__main__":
    window = MyWindow(1280, 720, "My Pyglet Window", resizable=True)
    pyglet.clock.schedule_interval(window.update, 1/30.0)
    pyglet.app.run()