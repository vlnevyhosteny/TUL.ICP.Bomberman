from collections import namedtuple
from src.game_field import GameField
from src.basic_helpers import get_positions_list
from src.game_config import TRACING_GRASS_CONSTANT
from src.textures import *

Edge = namedtuple('Edge', 'start_z, start_x, end_z, end_x, cost')


def make_edge(start_z, start_x, end_z, end_x, cost=1):
    return Edge(start_z, start_x, end_z, end_x, cost)


class TracingHelper:
    def __init__(self, game_field: GameField):
        self.game_field = game_field
        self.quantified_game_field = None

    def quantify_game_field(self):
        for position in get_positions_list():
            x, y, z = position

            dx = x - 1
            block = self.game_field.shown.get((dx, 0, z))
            if block is not None:
                if block == GRASS:
                    self.quantified_game_field.append(make_edge(z, x, z, dx, TRACING_GRASS_CONSTANT))
            else:
                self.quantified_game_field.append(make_edge(z, x, z, dx))

            dx = x + 1
            block = self.game_field.shown.get((dx, 0, z))
            if block is not None:
                if block == GRASS:
                    self.quantified_game_field.append(make_edge(z, x, z, dx, TRACING_GRASS_CONSTANT))
            else:
                self.quantified_game_field.append(make_edge(z, x, z, dx))

            dz = z - 1
            block = self.game_field.shown.get((x, 0, dz))
            if block is not None:
                if block == GRASS:
                    self.quantified_game_field.append(make_edge(z, x, dz, x, TRACING_GRASS_CONSTANT))
            else:
                self.quantified_game_field.append(make_edge(z, x, dz, x))

            dz = z + 1
            block = self.game_field.shown.get((x, 0, dz))
            if block is not None:
                if block == GRASS:
                    self.quantified_game_field.append(make_edge(z, x, dz, x, TRACING_GRASS_CONSTANT))
            else:
                self.quantified_game_field.append(make_edge(z, x, dz, x))

        pass

    def is_quantified(self):
        return self.quantified is not None

    def do_dijkstra(self, start_edge, destination_edge):
        if self.is_quantified() is False:
            self.quantified_game_field()

        pass
