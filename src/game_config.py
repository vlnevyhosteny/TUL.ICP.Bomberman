from pyglet.gl import GLfloat

TICKS_PER_SEC = 60

# Size of sectors used to ease block loading.
SECTOR_SIZE = 16

WALKING_SPEED = 5
FLYING_SPEED = 15

TERMINAL_VELOCITY = 50

PLAYER_HEIGHT = 1

HALF_OF_FIELD_SIZE = 5

STARTING_POSITION_X = 0
STARTING_POSITION_Y = 8
STARTING_POSITION_Z = -5

STATIC_LIGHT_POSITION = (20, 20, 20)

SHADOW_WIDTH = 50
SHADOW_HEIGHT = 20

STARTING_ROTATION_X = -180
STARTING_ROTATION_Y = -65

FACES = [
    (0, 1, 0),
    (0, -1, 0),
    (-1, 0, 0),
    (1, 0, 0),
    (0, 0, 1),
    (0, 0, -1),
]

TEXTURE_PATH = 'texture.png'

BOMB_STARTING_RANGE = 3
BOMB_TIMESPAN_SECS = 3

TRACING_GRASS_CONSTANT = 5

ambientLight = (GLfloat * 4)(0.2, 0.2, 0.2, 1.0)
diffuseLight = (GLfloat * 4)(0.7, 0.7, 0.7, 1.0)

INITIAL_BOMBS_COUNT = 1
