from __future__ import division

import sys
import math
import time

from collections import deque
from pyglet import image
from pyglet.gl import *
from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse

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

STARTING_ROTATION_X = -180
STARTING_ROTATION_Y = -65

if sys.version_info[0] >= 3:
    xrange = range


def cube_vertices(x, y, z, n):
    """ Return the vertices of the cube at position x, y, z with size 2*n.

    """
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # back
    ]


def tex_coord(x, y, n=4):
    """ Return the bounding vertices of the texture square.

    """
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m


def tex_coords(top, bottom, side):
    """ Return a list of the texture squares for the top, bottom and side.

    """
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top)
    result.extend(bottom)
    result.extend(side * 4)
    return result


TEXTURE_PATH = 'texture.png'

GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))

FACES = [
    (0, 1, 0),
    (0, -1, 0),
    (-1, 0, 0),
    (1, 0, 0),
    (0, 0, 1),
    (0, 0, -1),
]


def normalize(position):
    """ Accepts `position` of arbitrary precision and returns the block
    containing that position.

    Parameters
    ----------
    position : tuple of len 3

    Returns
    -------
    block_position : tuple of ints of len 3

    """
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return x, y, z


def sectorize(position):
    """ Returns a tuple representing the sector for the given `position`.

    Parameters
    ----------
    position : tuple of len 3

    Returns
    -------
    sector : tuple of len 3

    """
    x, y, z = normalize(position)
    x, y, z = x // SECTOR_SIZE, y // SECTOR_SIZE, z // SECTOR_SIZE
    return x, 0, z


def is_starting_position(x, z, field_size):
    field_size = field_size / 2

    if x in (-field_size + 1, field_size - 1) and z in (-field_size + 1, field_size - 1):
        return True
    if x in (-field_size + 2, field_size - 1) and z in (-field_size + 1, field_size - 1):
        return True
    if x in (-field_size + 1, field_size - 2) and z in (-field_size + 1, field_size - 1):
        return True
    if x in (-field_size + 1, field_size - 1) and z in (-field_size + 2, field_size - 1):
        return True
    if x in (-field_size + 1, field_size - 1) and z in (-field_size + 1, field_size - 2):
        return True

    return False


def pythagoras_get_c(a, b):
    return math.sqrt(a ^ 2 + b ^ 2)


def rotate(origin, point, angle):
    """
    Rotate a point by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)

    return qx, qy


class GameField(object):

    def __init__(self):

        # A Batch is a collection of vertex lists for batched rendering.
        self.batch = pyglet.graphics.Batch()

        # A TextureGroup manages an OpenGL texture.
        self.group = TextureGroup(image.load(TEXTURE_PATH).get_texture())

        # A mapping from position to the texture of the block at that position.
        # This defines all the blocks that are currently in the world.
        self.world = {}

        # Same mapping as `world` but only contains blocks that are shown.
        self.shown = {}

        # Mapping from position to a pyglet `VertextList` for all shown blocks.
        self._shown = {}

        # Mapping from sector to a list of positions inside that sector.
        self.sectors = {}

        # Simple function queue implementation. The queue is populated with
        # _show_block() and _hide_block() calls
        self.queue = deque()

        self._initialize()

    def _initialize(self):
        """ Initialize the world by placing all the blocks.

        """
        n = HALF_OF_FIELD_SIZE
        s = 1  # step size
        y = 0  # initial y height

        for x in xrange(-n, n + 1, s):
            for z in xrange(-n, n + 1, s):

                if is_starting_position(x, z, n * 2) is False:
                    if (x % 2) == 0 or (z % 2) == 0:
                        self.add_block((x, y, z), GRASS, immediate=False)
                    else:
                        self.add_block((x, y, z), STONE, immediate=False)

                self.add_block((x, y - 1, z), STONE, immediate=False)

                if x in (-n, n) or z in (-n, n):
                    # create outer walls.
                    for dy in xrange(0, 1):
                        self.add_block((x, y + dy, z), STONE, immediate=False)

    def exposed(self, position):
        """ Returns False is given `position` is surrounded on all 6 sides by
        blocks, True otherwise.

        """
        x, y, z = position

        for dx, dy, dz in FACES:

            if (x + dx, y + dy, z + dz) not in self.world:
                return True

        return False

    def add_block(self, position, texture, immediate=True):
        """ Add a block with the given `texture` and `position` to the world.

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position of the block to add.
        texture : list of len 3
            The coordinates of the texture squares. Use `tex_coords()` to
            generate.
        immediate : bool
            Whether or not to draw the block immediately.

        """
        if position in self.world:
            self.remove_block(position, immediate)

        self.world[position] = texture
        self.sectors.setdefault(sectorize(position), []).append(position)

        if immediate:
            if self.exposed(position):
                self.show_block(position)

            self.check_neighbors(position)

    def remove_block(self, position, immediate=True):
        """ Remove the block at the given `position`.

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position of the block to remove.
        immediate : bool
            Whether or not to immediately remove block from canvas.

        """
        del self.world[position]
        self.sectors[sectorize(position)].remove(position)

        if immediate:
            if position in self.shown:
                self.hide_block(position)

            self.check_neighbors(position)

    def check_neighbors(self, position):
        """ Check all blocks surrounding `position` and ensure their visual
        state is current. This means hiding blocks that are not exposed and
        ensuring that all exposed blocks are shown. Usually used after a block
        is added or removed.

        """
        x, y, z = position

        for dx, dy, dz in FACES:

            key = (x + dx, y + dy, z + dz)

            if key not in self.world:
                continue
            if self.exposed(key):
                if key not in self.shown:
                    self.show_block(key)
            else:
                if key in self.shown:
                    self.hide_block(key)

    def show_block(self, position, immediate=True):
        """ Show the block at the given `position`. This method assumes the
        block has already been added with add_block()

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position of the block to show.
        immediate : bool
            Whether or not to show the block immediately.

        """
        texture = self.world[position]
        self.shown[position] = texture

        if immediate:
            self._show_block(position, texture)
        else:
            self._enqueue(self._show_block, position, texture)

    def _show_block(self, position, texture):
        """ Private implementation of the `show_block()` method.

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position of the block to show.
        texture : list of len 3
            The coordinates of the texture squares. Use `tex_coords()` to
            generate.

        """
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(texture)

        # create vertex list
        self._shown[position] = self.batch.add(24, GL_QUADS, self.group, ('v3f/static', vertex_data),
                                               ('t2f/static', texture_data))

    def hide_block(self, position, immediate=True):
        """ Hide the block at the given `position`. Hiding does not remove the
        block from the world.

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position of the block to hide.
        immediate : bool
            Whether or not to immediately remove the block from the canvas.

        """
        self.shown.pop(position)

        if immediate:
            self._hide_block(position)
        else:
            self._enqueue(self._hide_block, position)

    def _hide_block(self, position):
        """ Private implementation of the 'hide_block()` method.

        """
        self._shown.pop(position).delete()

    def show_sector(self, sector):
        """ Ensure all blocks in the given sector that should be shown are
        drawn to the canvas.

        """
        for position in self.sectors.get(sector, []):

            if position not in self.shown and self.exposed(position):
                self.show_block(position, False)

    def hide_sector(self, sector):
        """ Ensure all blocks in the given sector that should be hidden are
        removed from the canvas.

        """
        for position in self.sectors.get(sector, []):

            if position in self.shown:
                self.hide_block(position, False)

    def change_sectors(self, before, after):
        """ Move from sector `before` to sector `after`. A sector is a
        contiguous x, y sub-region of world. Sectors are used to speed up
        world rendering.

        """
        before_set = set()
        after_set = set()
        pad = 4

        for dx in xrange(-pad, pad + 1):

            for dy in [0]:

                for dz in xrange(-pad, pad + 1):

                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                        continue
                    if before:
                        x, y, z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y, z = after
                        after_set.add((x + dx, y + dy, z + dz))

        show = after_set - before_set
        hide = before_set - after_set

        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.hide_sector(sector)

    def _enqueue(self, func, *args):
        """ Add `func` to the internal queue.

        """
        self.queue.append((func, args))

    def _dequeue(self):
        """ Pop the top function from the internal queue and call it.

        """
        func, args = self.queue.popleft()
        func(*args)

    def process_queue(self):
        """ Process the entire queue while taking periodic breaks. This allows
        the game loop to run smoothly. The queue contains calls to
        _show_block() and _hide_block() so this method should be called if
        add_block() or remove_block() was called with immediate=False

        """
        start = time.clock()

        while self.queue and time.clock() - start < 1.0 / TICKS_PER_SEC:
            self._dequeue()

    def process_entire_queue(self):
        """ Process the entire queue with no breaks.

        """
        while self.queue:
            self._dequeue()


class Window(pyglet.window.Window):

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)

        # Whether or not the window exclusively captures the mouse.
        self.exclusive = False

        # Strafing is moving lateral to the direction you are facing,
        # e.g. moving to the left or right while continuing to face forward.
        #
        # First element is -1 when moving forward, 1 when moving back, and 0
        # otherwise. The second element is -1 when moving left, 1 when moving
        # right, and 0 otherwise.
        self.strafe = [0, 0]

        # Current (x, y, z) position in the world, specified with floats. Note
        # that, perhaps unlike in math class, the y-axis is the vertical axis.
        self.position = (STARTING_POSITION_X, STARTING_POSITION_Y, STARTING_POSITION_Z)

        self.spectator_distance_to_center = pythagoras_get_c(HALF_OF_FIELD_SIZE, HALF_OF_FIELD_SIZE)

        # First element is rotation of the player in the x-z plane (ground
        # plane) measured from the z-axis down. The second is the rotation
        # angle from the ground plane up. Rotation is in degrees.
        #
        # The vertical plane rotation ranges from -90 (looking straight down) to
        # 90 (looking straight up). The horizontal rotation range is unbounded.
        self.rotation = (STARTING_ROTATION_X, STARTING_ROTATION_Y)
        self.rotate_horizontally = 0  # if -1 then rotate one step to left, if 1 to right
        self.rotate_vertically = 0  # if -1 then rotate one step to bottom, if 1 to top

        self.zoom = 0 # 1 zoom in, -1 zoom out

        self.reset_spectator = False # if True then return to starting position

        # Which sector the player is currently in.
        self.sector = None

        # Velocity in the y (upward) direction.
        self.dy = 0

        # Instance of the model that handles the world.
        self.model = GameField()

        # The label that is displayed in the top left of the canvas.
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18,
                                       x=10, y=self.height - 10, anchor_x='left', anchor_y='top', color=(0, 0, 0, 255))

        # This call schedules the `update()` method to be called
        # TICKS_PER_SEC. This is the main game event loop.
        pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)

    def set_exclusive_mouse(self, exclusive):
        """ If `exclusive` is True, the game will capture the mouse, if False
        the game will ignore the mouse.

        """
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive

    def get_sight_vector(self):
        """ Returns the current line of sight vector indicating the direction
        the player is looking.

        """
        x, y = self.rotation
        # y ranges from -90 to 90, or -pi/2 to pi/2, so m ranges from 0 to 1 and
        # is 1 when looking ahead parallel to the ground and 0 when looking
        # straight up or down.
        m = math.cos(math.radians(y))
        # dy ranges from -1 to 1 and is -1 when looking straight down and 1 when
        # looking straight up.
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return dx, dy, dz

    def get_motion_vector(self):
        """ Returns the current motion vector indicating the velocity of the
        player.

        Returns
        -------
        vector : tuple of len 3
            Tuple containing the velocity in x, y, and z respectively.

        """
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x + strafe)

            if self.flying:
                m = math.cos(y_angle)
                dy = math.sin(y_angle)

                if self.strafe[1]:
                    # Moving left or right.
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    # Moving backwards.
                    dy *= -1
                # When you are flying up or down, you have less left and right
                # motion.
                dx = math.cos(x_angle) * m
                dz = math.sin(x_angle) * m
            else:
                dy = 0.0
                dx = math.cos(x_angle)
                dz = math.sin(x_angle)

        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0

        return dx, dy, dz

    def if_needed_rotate_horizontally(self):
        if self.rotate_horizontally != 0:
            if self.rotate_horizontally == 1:  # right
                x, z = rotate((0, 0), (self.position[0], self.position[2]), math.radians(-1))

                self.position = (x, self.position[1], z)
                self.rotation = (self.rotation[0] - 1, self.rotation[1])
            elif self.rotate_horizontally == -1:  # left
                x, z = rotate((0, 0), (self.position[0], self.position[2]), math.radians(1))

                self.position = (x, self.position[1], z)
                self.rotation = (self.rotation[0] + 1, self.rotation[1])

    def if_needed_rotate_vertically(self):
        if self.rotate_vertically != 0:
            if self.rotate_vertically == 1 and self.rotation[1] > -90:
                z, y = rotate((0, 0), (self.position[2], self.position[1]), math.radians(-1))

                self.position = (self.position[0], y, z)
                self.rotation = (self.rotation[0], self.rotation[1] - 1)
            elif self.rotate_vertically == -1 and self.rotation[1] <= 90:
                z, y = rotate((0, 0), (self.position[2], self.position[1]), math.radians(1))

                self.position = (self.position[0], y, z)
                self.rotation = (self.rotation[0], self.rotation[1] + 1)

    def if_needed_zoom(self):
        if self.zoom != 0:
            x, y, z = self.position

            if self.zoom > 0:
                x, y, z = x - 0.1, y - 0.1, z - 0.1

                if x < 0:
                    x = 0
                if y < 0:
                    y = 0
                if z < 0:
                    z = 0

            elif self.zoom < 0:
                x, y, z = x + 0.1, y + 0.1, z + 0.1

            self.position = x, y, z

    def update(self, dt):
        """ This method is scheduled to be called repeatedly by the pyglet
        clock.

        Parameters
        ----------
        dt : float
            The change in time since the last call.

        """
        self.model.process_queue()
        sector = sectorize(self.position)

        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)

            if self.sector is None:
                self.model.process_entire_queue()

            self.sector = sector

        m = 8
        dt = min(dt, 0.2)

        for _ in xrange(m):
            self._update(dt / m)

    def _update(self, dt):
        """ Private implementation of the `update()` method. This is where most
        of the motion logic lives, along with gravity and collision detection.

        Parameters
        ----------
        dt : float
            The change in time since the last call.

        """
        # walking
        #speed = FLYING_SPEED if self.flying else WALKING_SPEED
        #d = dt * speed  # distance covered this tick.
        #dx, dy, dz = self.get_motion_vector()
        # New position in space, before accounting for gravity.
        #dx, dy, dz = dx * d, dy * d, dz * d
        # gravity

        self.if_needed_rotate_horizontally()
        self.if_needed_rotate_vertically()
        self.if_needed_zoom()

        if self.reset_spectator:
            self.position = (STARTING_POSITION_X, STARTING_POSITION_Y, STARTING_POSITION_Z)
            self.rotation = (STARTING_ROTATION_X, STARTING_ROTATION_Y)
            self.reset_spectator = False

    def collide(self, position, height):
        """ Checks to see if the player at the given `position` and `height`
        is colliding with any blocks in the world.

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position to check for collisions at.
        height : int or float
            The height of the player.

        Returns
        -------
        position : tuple of len 3
            The new position of the player taking into account collisions.

        """
        # How much overlap with a dimension of a surrounding block you need to
        # have to count as a collision. If 0, touching terrain at all counts as
        # a collision. If .49, you sink into the ground, as if walking through
        # tall grass. If >= .5, you'll fall through the ground.
        pad = 0.25
        p = list(position)
        np = normalize(position)

        for face in FACES:  # check all surrounding blocks
            for i in xrange(3):  # check each dimension independently

                if not face[i]:
                    continue

                # How much overlap you have with this dimension.
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue

                for dy in xrange(height):  # check each height

                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    if tuple(op) not in self.model.world:
                        continue

                    p[i] -= (d - pad) * face[i]

                    if face == (0, -1, 0) or face == (0, 1, 0):
                        # You are colliding with the ground or ceiling, so stop
                        # falling / rising.
                        self.dy = 0
                    break

        return tuple(p)

    def on_mouse_motion(self, x, y, dx, dy):
        """ Called when the player moves the mouse.

        Parameters
        ----------
        x, y : int
            The coordinates of the mouse click. Always center of the screen if
            the mouse is captured.
        dx, dy : float
            The movement of the mouse.

        """
        if self.exclusive:
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.zoom = scroll_y

    def on_key_press(self, symbol, modifiers):
        """ Called when the player presses a key. See pyglet docs for key
        mappings.

        Parameters
        ----------
        symbol : int
            Number representing the key that was pressed.
        modifiers : int
            Number representing any modifying keys that were pressed.

        """
        if symbol == key.W:
            self.strafe[0] -= 0 #1

        elif symbol == key.S:
            self.strafe[0] += 0 #1

        elif symbol == key.A:
            self.strafe[1] -= 0 #1

        elif symbol == key.D:
            self.strafe[1] += 0 #1

        elif symbol == key.SPACE:
            if self.dy == 0:
                self.dy = 0 #JUMP_SPEED

        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)

        elif symbol == key.RIGHT:
            self.rotate_horizontally = 1

        elif symbol == key.LEFT:
            self.rotate_horizontally = -1

        elif symbol == key.UP:
            self.rotate_vertically = 1

        elif symbol == key.DOWN:
            self.rotate_vertically = -1

        elif symbol == key.R:
            self.reset_spectator = True

    def on_key_release(self, symbol, modifiers):
        """ Called when the player releases a key. See pyglet docs for key
        mappings.

        Parameters
        ----------
        symbol : int
            Number representing the key that was pressed.
        modifiers : int
            Number representing any modifying keys that were pressed.

        """
        if symbol == key.W:
            self.strafe[0] += 0 #1

        elif symbol == key.S:
            self.strafe[0] -= 0 #1

        elif symbol == key.A:
            self.strafe[1] += 0 #1

        elif symbol == key.D:
            self.strafe[1] -= 0 #1

        elif symbol == key.RIGHT:
            self.rotate_horizontally = 0

        elif symbol == key.LEFT:
            self.rotate_horizontally = 0

        elif symbol == key.UP:
            self.rotate_vertically = 0

        elif symbol == key.DOWN:
            self.rotate_vertically = 0

    def on_resize(self, width, height):
        """ Called when the window is resized to a new `width` and `height`.

        """
        # label
        self.label.y = height - 10

        x, y = self.width // 2, self.height // 2
        n = 10

    def set_2d(self):
        """ Configure OpenGL to draw in 2d.

        """
        width, height = self.get_size()

        glDisable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_3d(self):
        """ Configure OpenGL to draw in 3d.

        """
        width, height = self.get_size()

        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        x, y = self.rotation

        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))

        x, y, z = self.position

        glTranslatef(-x, -y, -z)

    def on_draw(self):
        """ Called by pyglet to draw the canvas.

        """
        self.clear()
        self.set_3d()
        glColor3d(1, 1, 1)
        self.model.batch.draw()
        self.set_2d()
        self.draw_label()

    def draw_label(self):
        """ Draw the label in the top left of the screen.

        """
        x, y, z = self.position
        self.label.text = '%02d (%.2f, %.2f, %.2f) (%.2f, %.2f) %d / %d' % (
            pyglet.clock.get_fps(), x, y, z, self.rotation[0], self.rotation[1],
            len(self.model._shown), len(self.model.world))

        self.label.draw()


def opengl_setup():
    """ Basic OpenGL configuration.

    """
    # Set the color of "clear", i.e. the sky, in rgba.
    glClearColor(0.5, 0.69, 1.0, 1)
    # Enable culling (not rendering) of back-facing facets -- facets that aren't
    # visible to you.
    glEnable(GL_CULL_FACE)
    # Set the texture minification/magnification function to GL_NEAREST (nearest
    # in Manhattan distance) to the specified texture coordinates. GL_NEAREST
    # "is generally faster than GL_LINEAR, but it can produce textured images
    # with sharper edges because the transition between texture elements is not
    # as smooth."
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)


def main():
    window = Window(width=800, height=600, caption='Bomberman', resizable=True)
    # Hide the mouse cursor and prevent the mouse from leaving the window.
    window.set_exclusive_mouse(True)
    opengl_setup()
    pyglet.app.run()


if __name__ == '__main__':
    main()
