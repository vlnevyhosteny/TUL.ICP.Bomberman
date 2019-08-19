from __future__ import division

from pyglet.gl import *
from pyglet.window import key

from src.basic_helpers import *
from src.game_field import GameField
from src.game_config import *
from src.tracing_helper import TracingHelper

from src.basic_helpers import m3d_rad_to_deg
from src.game_config import STATIC_LIGHT_POSITION, SHADOW_WIDTH, SHADOW_HEIGHT

from math import sqrt, atan


class Window(pyglet.window.Window):

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)

        # Whether or not the window exclusively captures the mouse.
        self.exclusive = False

        self.fullscreen_request = False

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

        self.strips = None
        self.texture_matrix = M3DMatrix44f()

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

        self.player_wants_place_bomb = False

        self.game_stopped = False

        # Instance of the model that handles the world.
        self.model = GameField()

        # The label that is displayed in the top left of the canvas.
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18,
                                       x=10, y=self.height - 10, anchor_x='left', anchor_y='top', color=(0, 0, 0, 255))

        self.status = pyglet.text.Label('', font_name='Arial', font_size=50, x=self.width//2, y=self.height//2,
                                        anchor_x='center', anchor_y='center', color=(0, 0, 0, 255))

        self.regenerate_shadow_map()

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

    def game_over(self):
        self.status.text = 'Game Over!'
        self.game_stopped = True

    def game_win(self):
        self.status.text = 'Win!'
        self.game_stopped = True

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
        if all(figure.hit for figure in self.model.npc_figures): self.game_win()
        #if self.model.player_figure.hit: self.game_over()

        self.move_figures(dt)
        self.place_bombs()

        self.if_needed_rotate_horizontally()
        self.if_needed_rotate_vertically()
        self.if_needed_zoom()

        if self.fullscreen_request:
            self.set_fullscreen(not self.fullscreen)
            self.fullscreen_request = False

        if self.reset_spectator:
            self.position = (STARTING_POSITION_X, STARTING_POSITION_Y, STARTING_POSITION_Z)
            self.rotation = (STARTING_ROTATION_X, STARTING_ROTATION_Y)
            self.reset_spectator = False

    def move_figures(self, dt):
        distance = dt * WALKING_SPEED  # distance covered this tick.

        self.npcs_action(distance)

        if self.strafe[0] != 0 or self.strafe[1] != 0:
            new_x = self.model.player_figure.position_x
            new_z = self.model.player_figure.position_z

            if self.strafe[0] == 1:  # right
                new_x += distance
            elif self.strafe[0] == -1:
                new_x -= distance

            if self.strafe[1] == 1:  # top
                new_z += distance
            elif self.strafe[1] == -1:
                new_z -= distance

            if not self.model.check_if_figure_collide(new_x, new_z):
                self.model.player_figure.position_x = new_x
                self.model.player_figure.position_z = new_z

                self.model.player_figure.recalculate_vertices()

    def npcs_action(self, distance):
        for figure in self.model.npc_figures:
            running_away = False

            for bomb in self.model.bombs:
                if any(round(figure.position_x) == position[0] and
                       round(figure.position_z) == position[1]
                       for position in bomb.positions_affected_by_bomb):

                    running_away = self.escape_with_figure(bomb, figure, distance)

            if not running_away:
                self.place_bombs_with_figure(figure, distance)

    def place_bombs_with_figure(self, figure, distance):
        coef = 0.5

        path = self.model.tracing_helper\
            .do_dijkstra((figure.position_x, 0, figure.position_z),
                         (self.model.player_figure.position_x, 0, self.model.player_figure.position_z))

        x, z = self.model.tracing_helper.get_direction_from_path(path)

        if x == -1:
            rounded_x = round(figure.position_x - distance)

            if not self.model.check_if_figure_collide(rounded_x - coef, figure.position_z) and \
               not self.is_position_affected_by_any_bomb(rounded_x, figure.position_z):
                figure.position_x -= distance
                figure.recalculate_vertices()
            else:
                return self.npc_place_bomb(figure)

        if x == 1:
            rounded_x = round(figure.position_x + distance)

            if not self.model.check_if_figure_collide(rounded_x + coef, figure.position_z) and \
               not self.is_position_affected_by_any_bomb(rounded_x, figure.position_z):
                figure.position_x += distance
                figure.recalculate_vertices()
            else:
                return self.npc_place_bomb(figure)

        if z == -1:
            rounded_z = round(figure.position_z - distance)

            if not self.model.check_if_figure_collide(figure.position_x, rounded_z - coef) and \
               not self.is_position_affected_by_any_bomb(figure.position_x, rounded_z):
                figure.position_z -= distance
                figure.recalculate_vertices()
            else:
                return self.npc_place_bomb(figure)

        if z == 1:
            rounded_z = round(figure.position_z + distance)

            if not self.model.check_if_figure_collide(figure.position_x, rounded_z + coef) and \
               not self.is_position_affected_by_any_bomb(figure.position_x, rounded_z):
                figure.position_z += distance
                figure.recalculate_vertices()
            else:
                return self.npc_place_bomb(figure)

    def is_position_affected_by_any_bomb(self, x, z):
        for bomb in self.model.bombs:
            if any(round(x) == position[0] and
                   round(z) == position[1]
                   for position in bomb.positions_affected_by_bomb):
                return True

    def escape_with_figure(self, bomb, figure, distance):
        coef = 0

        if figure.escaping_to is None:
            figure.escaping_to = self.find_escape_location(bomb, figure)

            if figure.escaping_to is None:
                return True

        path = self.model.tracing_helper.do_dijkstra((get_int_from_float(figure.position_x),
                                                      0, get_int_from_float(figure.position_z)),
                                                     figure.escaping_to)

        x, z = self.model.tracing_helper.get_direction_from_path(path)

        if x == 0 and z == 0:
            if round(figure.position_x) != figure.escaping_to[0] or \
               round(figure.position_z) != figure.escaping_to[2]:
                x, z = figure.previous_direction
            else:
                return False

        figure.previous_direction = x, z

        if x == -1:
            rounded_x = round(figure.position_x - distance)

            if not self.model.check_if_figure_collide(rounded_x - coef, figure.position_z):
                figure.position_x -= distance
                figure.recalculate_vertices()
                return True

        if x == 1:
            rounded_x = round(figure.position_x + distance)

            if not self.model.check_if_figure_collide(rounded_x + coef, figure.position_z):
                figure.position_x += distance
                figure.recalculate_vertices()
                return True

        if z == -1:
            rounded_z = round(figure.position_z - distance)

            if not self.model.check_if_figure_collide(figure.position_x, rounded_z - coef):
                figure.position_z -= distance
                figure.recalculate_vertices()
                return True

        if z == 1:
            rounded_z = round(figure.position_z + distance)

            if not self.model.check_if_figure_collide(figure.position_x, rounded_z + coef):
                figure.position_z += distance
                figure.recalculate_vertices()
                return True

        return False

    def find_escape_location(self, bomb, figure):
        for i in range(1, HALF_OF_FIELD_SIZE * 2, 1):
            for dx in xrange(round(figure.position_x) - i, round(figure.position_x) + i, 1):
                for dz in xrange(round(figure.position_z) - i, round(figure.position_z) + i, 1):
                    if dx != bomb.position_x and dz != bomb.position_z and \
                        not any(round(dx) == position[0] and
                                round(dz) == position[1]
                                for position in bomb.positions_affected_by_bomb):
                        if not self.model.check_if_figure_collide(dx, dz):
                            return dx, 0, dz

    def place_bombs(self):
        if self.player_wants_place_bomb and not self.game_stopped:
            new_bomb = self.model.player_figure.place_bomb()

            if new_bomb is not None:  # Can be None in case of unable to place bomb
                new_bomb.calculate_affection_of_bomb(self.model._shown)

                new_bomb.gl_bomb = self.model.draw_bomb(new_bomb)
                new_bomb.timer = pyglet.clock.schedule_once(self.model.detonation, new_bomb.timespan)
                self.model.bombs.append(new_bomb)

        self.player_wants_place_bomb = False

    def npc_place_bomb(self, figure):
        if not self.game_stopped:
            new_bomb = figure.place_bomb()

            if new_bomb is not None:
                new_bomb.calculate_affection_of_bomb(self.model._shown)

                figure.previous_direction = None

                new_bomb.gl_bomb = self.model.draw_bomb(new_bomb)
                new_bomb.timer = pyglet.clock.schedule_once(self.model.detonation, new_bomb.timespan)
                self.model.bombs.append(new_bomb)


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
            self.strafe[1] = 1

        if symbol == key.S:
            self.strafe[1] = -1

        if symbol == key.A:
            self.strafe[0] = 1

        if symbol == key.D:
            self.strafe[0] = -1

        elif symbol == key.SPACE:
            self.player_wants_place_bomb = True

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

        elif symbol == key.F:
            self.fullscreen_request = True

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
            self.strafe[1] = 0

        if symbol == key.S:
            self.strafe[1] = 0

        if symbol == key.A:
            self.strafe[0] = 0

        if symbol == key.D:
            self.strafe[0] = 0

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
        self.model.main_batch.draw()
        self.model.bomb_batch.draw()
        self.set_2d()
        self.draw_label()
        self.status.draw()

    def draw_label(self):
        """ Draw the label in the top left of the screen.

        """
        x, y, z = self.position
        self.label.text = '%02d (%.2f, %.2f, %.2f) (%.2f, %.2f) %d / %d' % (
            pyglet.clock.get_fps(), self.model.player_figure.position_x, 0, self.model.player_figure.position_z,
            self.rotation[0], self.rotation[1], len(self.model._shown), len(self.model.world))

        self.label.draw()

    def regenerate_shadow_map(self):
        global textureMatrix, strips
        lightModelview = (GLfloat * 16)()
        lightProjection = (GLfloat * 16)()
        sceneBoundingRadius = 95.0  # based on objects in scene

        # Save the depth precision for where it's useful
        lightToSceneDistance = sqrt(STATIC_LIGHT_POSITION[0] * STATIC_LIGHT_POSITION[0] + STATIC_LIGHT_POSITION[1] *
                                    STATIC_LIGHT_POSITION[1] + STATIC_LIGHT_POSITION[2] * STATIC_LIGHT_POSITION[2])
        nearPlane = lightToSceneDistance - sceneBoundingRadius

        # Keep the scene filling the depth texture
        fieldOfView = m3d_rad_to_deg(2.0 * atan(sceneBoundingRadius / lightToSceneDistance))

        # Switch to light's point of view
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(STATIC_LIGHT_POSITION[0], STATIC_LIGHT_POSITION[1], STATIC_LIGHT_POSITION[2], 0.0, 0.0, 0.0, 0.0, 1.0,
                  0.0)
        glGetFloatv(GL_MODELVIEW_MATRIX, lightModelview)
        glViewport(0, 0, SHADOW_WIDTH, SHADOW_HEIGHT)

        # Clear the depth buffer only
        glClear(GL_DEPTH_BUFFER_BIT)

        # All we care about here is resulting depth values
        glShadeModel(GL_FLAT)
        glDisable(GL_LIGHTING)
        glDisable(GL_COLOR_MATERIAL)
        glDisable(GL_NORMALIZE)
        glColorMask(0, 0, 0, 0)

        # Overcome imprecision
        glEnable(GL_POLYGON_OFFSET_FILL)

        # Draw objects in the scene except base plane
        # which never shadows anything
        self.set_3d()
        glColor3d(1, 1, 1)
        self.model.main_batch.draw()
        self.model.bomb_batch.draw()

        # Copy depth values into depth texture
        #glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, 0, 0, SHADOW_WIDTH, SHADOW_HEIGHT, 0)

        # Restore normal drawing state
        glShadeModel(GL_SMOOTH)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_NORMALIZE)
        glColorMask(1, 1, 1, 1)
        glDisable(GL_POLYGON_OFFSET_FILL)

        # Set up texture matrix for shadow map projection,
        # which will be rolled into the eye linear
        # texture coordinate generation plane equations
        tempMatrix = M3DMatrix44f()
        m3d_load_identity44(tempMatrix)
        m3d_translate_matrix44(tempMatrix, 0.5, 0.5, 0.5)
        m3d_scale_matrix44(tempMatrix, 0.5, 0.5, 0.5)
        m3d_matrix_multiply44(self.texture_matrix, tempMatrix, lightProjection)
        m3d_matrix_multiply44(tempMatrix, self.texture_matrix, lightModelview)

        # transpose to get the s, t, r, and q rows for plane equations
        m3d_transpose_matrix44(self.texture_matrix, tempMatrix)
        # this seems sorta awkward, but I haven't hit on a better way to index into the array in a fashion that
        # pyglet will work with.
        self.strips = [(GLfloat * 4)(self.texture_matrix[4], self.texture_matrix[5], self.texture_matrix[6], self.texture_matrix[7]),
                  (GLfloat * 4)(self.texture_matrix[8], self.texture_matrix[9], self.texture_matrix[10], self.texture_matrix[11]),
                  (GLfloat * 4)(self.texture_matrix[12], self.texture_matrix[13], self.texture_matrix[14], self.texture_matrix[15]),]


def opengl_setup():
    """ Basic OpenGL configuration.

    """
    # Set the color of "clear", i.e. the sky, in rgba.
    glClearColor(0.5, 0.69, 1.0, 1)
    # Enable culling (not rendering) of back-facing facets -- facets that aren't
    # visible to you.
    glEnable(GL_CULL_FACE)

    # Set up some lighting state that never changes
    glShadeModel(GL_SMOOTH)
    glEnable(GL_LIGHTING)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_NORMALIZE)
    glEnable(GL_LIGHT0)

    glBindTexture(GL_TEXTURE_2D, GLuint(0))
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    # Set the texture minification/magnification function to GL_NEAREST (nearest
    # in Manhattan distance) to the specified texture coordinates. GL_NEAREST
    # "is generally faster than GL_LINEAR, but it can produce textured images
    # with sharper edges because the transition between texture elements is not
    # as smooth."
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    glTexGeni(GL_S, GL_TEXTURE_GEN_MODE, GL_EYE_LINEAR)
    glTexGeni(GL_T, GL_TEXTURE_GEN_MODE, GL_EYE_LINEAR)
    glTexGeni(GL_R, GL_TEXTURE_GEN_MODE, GL_EYE_LINEAR)
    glTexGeni(GL_Q, GL_TEXTURE_GEN_MODE, GL_EYE_LINEAR)


def main():
    window = Window(width=800, height=600, caption='Bomberman', resizable=True, fullscreen=True)
    # Hide the mouse cursor and prevent the mouse from leaving the window.
    window.set_exclusive_mouse(True)
    opengl_setup()
    pyglet.app.run()


if __name__ == '__main__':
    main()
