from src.basic_helpers import cube_vertices, get_int_from_float
from src.game_config import BOMB_STARTING_RANGE, BOMB_TIMESPAN_SECS, INITIAL_BOMBS_COUNT
from src.bomb import Bomb


class BaseFigure:
    def __init__(self, position_x, position_z):
        self.position_x = position_x
        self.position_z = position_z
        self.gl_object = None
        self.bomb_count = 1
        self.placed_bombs = 0
        self.bombs = self.generate_bombs()
        self.hit = False
        self.previous_direction = None

    def recalculate_vertices(self):
        if self.gl_object is not None:
            self.gl_object.vertices = cube_vertices(self.position_x, 0, self.position_z, 0.25)

        self.reposition_not_active_bombs()

    def place_bomb(self):
        for bomb in self.bombs:
            if not bomb.active:
                bomb.active = True
                self.placed_bombs += 1

                bomb.position_z = get_int_from_float(bomb.position_z)
                bomb.position_x = get_int_from_float(bomb.position_x)

                return bomb

        return None

    def remove_bomb(self, bomb):
        self.placed_bombs -= 1

    def generate_bombs(self):
        result = []

        for i in range(0, INITIAL_BOMBS_COUNT, 1):
            result.append(Bomb(self, self.position_x, self.position_z, BOMB_STARTING_RANGE, BOMB_TIMESPAN_SECS))

        return result

    def get_normalized_positions(self, coef=0.25):
        x = self.position_x
        z = self.position_z

        if x > 0:
            x -= coef
        else:
            x += coef

        if z > 0:
            z -= coef
        else:
            z += coef

        return x, z

    def reposition_not_active_bombs(self):
        for bomb in self.bombs:
            if not bomb.active and bomb.gl_object is not None:
                bomb.position_x = self.position_x
                bomb.position_z = self.position_z

                bomb.recalculate_vertices()
