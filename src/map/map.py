from typing import List, Tuple
import pyglet
from past.builtins import xrange
from pyglet.gl import GL_QUADS

from src.map.cube import Cube
from src.map.cube_style import CubeStyle

CUBE_FACES: List[Tuple[int, int, int]] = [
    (0, 1, 0),
    (0, -1, 0),
    (-1, 0, 0),
    (1, 0, 0),
    (0, 0, 1),
    (0, 0, -1),
]

background = pyglet.graphics.OrderedGroup(0)
foreground = pyglet.graphics.OrderedGroup(1)


class Map:
    def __init__(self, name, width, height, cubes, cube_styles, floor_cubes, border):
        self.name = name
        self.width = width
        self.height = height
        self.cubes_list = cubes
        self.cube_styles = cube_styles
        self.floor_cubes_list = floor_cubes
        self.border = border

        self.cubes = self.cubes_list_to_2d_array(cubes, width, height)
        self.floor_cubes = self.cubes_list_to_2d_array(floor_cubes, width, height)

        self.batch = pyglet.graphics.Batch()

    def initialize(self):
        # floor
        for x in xrange(0, self.height, 1):
            for y in xrange(0, self.width, 1):
                cube_config = self.floor_cubes[x][y]
                #cube_style = next(s for s in self.cube_styles if s.style_id == cube_config.style_id)

                self.create_cube(x, y, 0)

        # field
        for x in xrange(0, self.height, 1):
            for y in xrange(0, self.width, 1):
                cube_config = self.cubes[x][y]
                cube_style = next(s for s in self.cube_styles if s.style_id == cube_config.style_id)

                self.create_cube(x, y, 1)
                
    def create_cube(self, x: int, y: int, z: int) -> None:
        vertex = Map.cube_vertices(x, y, z, 0.5)

        self.batch.add(24, GL_QUADS, foreground, ('v3f/static', vertex))

    @staticmethod
    def cube_vertices(x, y, z, n):
        return [
            x - n, y - n, z - n,  x + n, y - n, z - n,  x + n, y - n, z + n,  x - n, y - n, z + n,  # bottom
            x - n, y - n, z - n,  x - n, y - n, z + n,  x - n, y + n, z + n,  x - n, y + n, z - n,  # left
            x - n, y + n, z - n,  x - n, y + n, z + n,  x + n, y + n, z + n,  x + n, y + n, z - n,  # top
            x + n, y - n, z + n,  x + n, y - n, z - n,  x + n, y + n, z - n,  x + n, y + n, z + n,  # right
            x - n, y - n, z + n,  x + n, y - n, z + n,  x + n, y + n, z + n,  x - n, y + n, z + n,  # front
            x + n, y - n, z - n,  x - n, y - n, z - n,  x - n, y + n, z - n,  x + n, y + n, z - n,  # back
        ]

    @staticmethod
    def cubes_list_to_2d_array(cubes_list: [], width: int, height: int) -> [[]]:
        cube_2d_array = [[]]

        for x in xrange(0, width):
            row = [c for c in cubes_list if c.position_x == x]

            if len(row) != height:
                raise ValueError('Not all cubes are defined in map.')

            cube_2d_array.append(row)

        cube_2d_array.pop(0)

        return cube_2d_array

