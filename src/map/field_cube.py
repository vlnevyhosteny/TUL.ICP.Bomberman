from src.map.cube import Cube


class FieldCube(Cube):
    def __init__(self, position_x, position_y, style_id, is_solid):
        super(FieldCube, self).__init__(position_x, position_y, style_id)
        self.is_solid = is_solid
        self.is_empty = False

    def set_as_empty(self):
        self.is_empty = True
