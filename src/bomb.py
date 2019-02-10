class Bomb:
    def __init__(self, position_x, position_z, range, timespan):
        self.position_x = position_x
        self.position_z = position_z
        self.range = range
        self.timespan = timespan
        self.gl_bomb = None
        self.timer = None

    def detonation(self, dt):
        del self
