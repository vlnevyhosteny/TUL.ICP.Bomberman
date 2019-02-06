from src.basic_helpers import cube_vertices


class BaseFigure:
    def __init__(self, position_x, position_z):
        self.position_x = position_x
        self.position_z = position_z
        self.gl_object = None

    def recalculate_vertices(self):
        if self.gl_object is not None:
            self.gl_object.vertices = cube_vertices(self.position_x, 0, self.position_z, 0.25)
