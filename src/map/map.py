from typing import List, Tuple

import pyglet

CUBE_FACES: List[Tuple[int, int, int]] = [
    (0, 1, 0),
    (0, -1, 0),
    (-1, 0, 0),
    (1, 0, 0),
    (0, 0, 1),
    (0, 0, -1),
]


class Map:
    def __init__(self, name, width, height, cubes, cube_styles, floor_cubes, border):
        self.name = name
        self.width = width
        self.height = height
        self.cubes = cubes
        self.cube_styles = cube_styles
        self.floor_cubes = floor_cubes
        self.border = border

        self.batch = pyglet.graphics.Batch()

    def draw(self):
        pass

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
