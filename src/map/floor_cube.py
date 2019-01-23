from src.map.cube import Cube


class FloorCube(Cube):
    def __init__(self, position_x, position_y, style_id):
        super(FloorCube, self).__init__(position_x, position_y, style_id)
