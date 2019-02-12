class Bomb:
    def __init__(self, figure, position_x, position_z, range, timespan):
        self.figure = figure
        self.position_x = position_x
        self.position_z = position_z
        self.range = range
        self.timespan = timespan
        self.gl_bomb = None
        self.timer = None
