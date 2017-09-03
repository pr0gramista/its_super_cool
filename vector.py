import math


class Vector():
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def xyz(self):
        return [self.x, self.y, self.z]

    def dist(self, b):
        return math.hypot(math.hypot(self.x - b.x, self.y - b.y), self.z - b.z)

    def copy(self):
        return Vector(self.x, self.y, self.z)
