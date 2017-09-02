from common.settings import SPECTATORS
from common.vector import Vector


class Player():
    def __init__(self, name):
        self.name = name
        self.team = SPECTATORS
        self.position = Vector(0, 0, 0)
        self.velocity = Vector(0, 0, 0)
