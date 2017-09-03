import pygame
import utils

from vector import Vector

class Tile(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("assets/groundTile_NE.png").convert_alpha()
        self.rect = self.image.get_rect()

class Gate(pygame.sprite.Sprite):
    def __init__(self, number):
        super().__init__()

        gate_height = {
            1: 48,
            2: 64,
            3: 56
        }

        gate_positions = {
            1: Vector(0.19592592592592592, -0.1559259259259259, 0),
            2: Vector(0.5624074074074075, -0.0024074074074074137, 0),
            3: Vector(1.1218518518518519, -0.08185185185185184, 0),
            4: Vector(0.24537037037037024, 4.75462962962963, 0),
            5: Vector(0.6072222222222221, 4.9127777777777775, 0),
            6: Vector(1.1700000000000002, 4.836666666666667, 0),
        }

        gtype = number
        if number > 3:
            gtype = number - 3

        self.image = pygame.transform.scale(pygame.image.load("assets/gate{}.png".format(gtype)).convert_alpha(), (25, gate_height[gtype]))
        self.rect = self.image.get_rect()

        self.position = gate_positions[number].copy()
        self.rect.x, self.rect.y = utils.get_position(*self.position.xyz())


class ConsoleTop(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load("assets/console_top.png").convert_alpha(), (1302, 1146))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = -200
        self.position = Vector(-5, -100, 0)

class ConsoleBottom(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load("assets/console_bottom.png").convert_alpha(), (1302, 1146))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = -200
        self.position = Vector(-5, -100, 0)