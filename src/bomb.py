from src.game_config import BOMB_STARTING_RANGE
from src.basic_helpers import cube_vertices


class Bomb:
    def __init__(self, figure, position_x, position_z, range, timespan):
        self.figure = figure
        self.position_x = position_x
        self.position_z = position_z
        self.range = range
        self.timespan = timespan
        self.gl_object = None
        self.timer = None
        self.active = False
        self.positions_affected_by_bomb = []

    def calculate_affection_of_bomb(self, _shown):
        self.positions_affected_by_bomb = []

        for i in range(self.position_x, self.position_x + BOMB_STARTING_RANGE):
            if _shown.get((i, 0, self.position_z)) is None:
                self.positions_affected_by_bomb.append((i, self.position_z))
            else:
                break

        for i in range(self.position_x, self.position_x - BOMB_STARTING_RANGE, -1):
            if _shown.get((i, 0, self.position_z)) is None:
                self.positions_affected_by_bomb.append((i, self.position_z))
            else:
                break

        for i in range(self.position_z, self.position_z + BOMB_STARTING_RANGE):
            if _shown.get((self.position_x, 0, i)) is None:
                self.positions_affected_by_bomb.append((self.position_x, i))
            else:
                break

        for i in range(self.position_z, self.position_z - BOMB_STARTING_RANGE, -1):
            if _shown.get((self.position_x, 0, i)) is None:
                self.positions_affected_by_bomb.append((self.position_x, i))
            else:
                break

    def recalculate_vertices(self):
        if self.gl_object is not None:
            self.gl_object.vertices = cube_vertices(self.position_x, 0, self.position_z, 0.25)
