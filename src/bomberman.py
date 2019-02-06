from __future__ import division

from past.builtins import xrange
from pyglet.gl import *
from pyglet.window import key

from src.basic_helpers import *
from src.game_field import GameField
from src.game_config import *


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

        self.zoom = 0  # 1 zoom in, -1 zoom out

        self.reset_spectator = False  # if True then return to starting position

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
            strafe = math.degrees(math.atan2(*self.strafe))
            x_angle = math.radians(strafe)

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
        speed = WALKING_SPEED
        distance = dt * speed  # distance covered this tick.
        dx, dy, dz = self.get_motion_vector()
        # New position in space, before accounting for gravity.
        dx, dy, dz = dx * distance, dy * distance, dz * distance

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
            self.strafe[0] -= 0  # 1

        elif symbol == key.S:
            self.strafe[0] += 0  # 1

        elif symbol == key.A:
            self.strafe[1] -= 0  # 1

        elif symbol == key.D:
            self.strafe[1] += 0  # 1

        elif symbol == key.SPACE:
            pass

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
            self.strafe[0] += 0  # 1

        elif symbol == key.S:
            self.strafe[0] -= 0  # 1

        elif symbol == key.A:
            self.strafe[1] += 0  # 1

        elif symbol == key.D:
            self.strafe[1] -= 0  # 1

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
