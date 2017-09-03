import pygame
import settings
import utils
from vector import Vector


class BallDummy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = utils.load_image("assets/meteorFullRound_NE.png", 0.15)
        self.rect = self.image.get_rect()
        self.position = Vector(0, 0, 0)
        self.velocity = Vector(0, 0, 0)
        self.speed = 1
        self.grabbed = False
        self.grabbed_by = None

    def update(self, delta):
        if self.grabbed == False:
            self.velocity.z -= delta * settings.GRAVITY

            self.position.x += delta * self.velocity.x
            self.position.y += delta * self.velocity.y
            self.position.z += delta * self.velocity.z

            bounce_x, bounce_y, bounce_z = utils.bounce_to_map(*self.position.xyz())
            self.pos_x, self.pos_y, self.pos_z = utils.cut_to_map(*self.position.xyz())

            self.velocity.x *= bounce_x
            self.velocity.y *= bounce_y
            self.velocity.z *= bounce_z
        else:
            pass

        self.rect.x, self.rect.y = utils.get_position(*self.position.xyz())


class BallShadow(pygame.sprite.Sprite):
    def __init__(self, ball):
        super().__init__()
        self.image = utils.load_image("assets/meteorFull_NE_shadow.png", 0.15)
        self.rect = self.image.get_rect()
        self.position = Vector(0, 0, 0)
        self.ball = ball

    def update(self):
        self.position.x = self.ball.position.x
        self.position.y = self.ball.position.y
        self.position.z = 0

        self.rect.x, self.rect.y = utils.get_position(*self.position.xyz())
