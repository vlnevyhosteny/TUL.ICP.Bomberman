from src.basic_helpers import cube_vertices, get_int_from_float
from src.game_config import BOMB_STARTING_RANGE, BOMB_TIMESPAN_SECS
from src.bomb import Bomb


class BaseFigure:
    def __init__(self, position_x, position_z):
        self.position_x = position_x
        self.position_z = position_z
        self.gl_object = None
        self.bomb_count = 1
        self.placed_bombs = []

    def recalculate_vertices(self):
        if self.gl_object is not None:
            self.gl_object.vertices = cube_vertices(self.position_x, 0, self.position_z, 0.25)

    def place_bomb(self):
        if len(self.placed_bombs) < self.bomb_count:
            position_x = get_int_from_float(self.position_x)
            position_z = get_int_from_float(self.position_z)

            new_bomb = Bomb(position_x, position_z, BOMB_STARTING_RANGE, BOMB_TIMESPAN_SECS)
            self.placed_bombs.append(new_bomb)

            return new_bomb
        else:
            return None

    def remove_bomb(self, bomb):
        self.placed_bombs.remove(bomb)

