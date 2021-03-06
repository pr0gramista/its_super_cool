import math
import time
import settings
import pygame

import utils
from vector import Vector


class Hero(pygame.sprite.Sprite):
    def __init__(self, id, team):
        super().__init__()
        SCALE = 0.5

        if team == 0:
            self.images = {
                180: utils.load_image("assets/astronaut_NW.png", SCALE),
                135: utils.load_image("assets/astronaut_N.png", SCALE),
                90: utils.load_image("assets/astronaut_NE.png", SCALE),
                -135: utils.load_image("assets/astronaut_W.png", SCALE),
                45: utils.load_image("assets/astronaut_E.png", SCALE),
                -90: utils.load_image("assets/astronaut_SW.png", SCALE),
                -45: utils.load_image("assets/astronaut_S.png", SCALE),
                0: utils.load_image("assets/astronaut_SE.png", SCALE)
            }
        else:
            self.images = {
                180: utils.load_image("assets/alien_NW.png", SCALE),
                135: utils.load_image("assets/alien_N.png", SCALE),
                90: utils.load_image("assets/alien_NE.png", SCALE),
                -135: utils.load_image("assets/alien_W.png", SCALE),
                45: utils.load_image("assets/alien_E.png", SCALE),
                -90: utils.load_image("assets/alien_SW.png", SCALE),
                -45: utils.load_image("assets/alien_S.png", SCALE),
                0: utils.load_image("assets/alien_SE.png", SCALE)
            }
        self.team = team
        self.id = id
        self.image = self.images[45]
        self.rect = self.image.get_rect()
        self.velocity = Vector(0, 0, 0)
        self.position = Vector(0, 0, 0)
        self.movement = Vector(0, 0, 0)
        self.speed = 0.75
        self.speed_holding = 0.5

        self.throws = False
        self.holds_ball = False
        self.stunned = False

        self.connection_handler = None
        self.input_handler = None
        self.game = None

    def move_up(self, stop=False):
        self.move(135, stop=stop)

    def move_down(self, stop=False):
        self.move(315, stop=stop)

    def move_right(self, stop=False):
        self.move(45, stop=stop)

    def move_left(self, stop=False):
        self.move(225, stop=stop)

    def grab(self):
        if self.game.ball.grabbed == False and self.game.ball.position.dist(self.position) < settings.GRAB_RANGE:
            self.connection_handler.grab(self)

    def throw(self, power):
        if self.game.ball.grabbed and self.game.ball.grabbed_by == self:
            self.connection_handler.throw(self, power)

    def update_pos(self):
        self.connection_handler.send({
            'operation': 'move',
            'id': self.id,
            'x': self.position.x,
            'y': self.position.y,
            'z': self.position.z,
            'vel_x': self.movement.x,
            'vel_y': self.movement.y,
            'vel_z': self.movement.z,
        })

    def beat(self):
        if self.game.ball.grabbed_by.position.dist(self.position) < settings.HIT_RANGE:
            self.connection_handler.beat(self)

    def throwing(self):
        self.connection_handler.throwing(self, self.hold)

    def update(self, delta):
        if self.stunned == False:
            if not self.holds_ball:
                self.velocity.x = self.movement.x * self.speed
                self.velocity.y = self.movement.y * self.speed
            else:
                self.velocity.x = self.movement.x * self.speed_holding
                self.velocity.y = self.movement.y * self.speed_holding

            self.position.x += delta * self.velocity.x
            self.position.y += delta * self.velocity.y

            self.position.x, self.position.y, self.position.z = utils.cut_to_map(*self.position.xyz())

            if round(self.movement.x, 2) == 0 and round(self.movement.y, 2) == 0:
                pass
            else:
                angle = round(math.degrees(math.atan2(self.velocity.y, self.velocity.x)))
                if angle in self.images:
                    self.image = self.images[angle]
        else:
            self.stunned = not time.time() > self.stun_time

            if self.change_image_to_stunned:
                self.image = pygame.transform.rotate(self.image, 90)
                self.change_image_to_stunned = False

        self.rect.x, self.rect.y = utils.get_position(*self.position.xyz())

    def stun(self, duration):
        self.stunned = True
        self.change_image_to_stunned = True
        self.stun_time = time.time() + duration
        # We can't perform image rotation here, because of:
        # 'pygame.error: Surfaces must not be locked during blit'

    def move(self, angle, stop=False):
        modifier = 1
        if stop:
            modifier = -1

        self.movement.x += modifier * math.cos(math.radians(angle))
        self.movement.y += modifier * math.sin(math.radians(angle))
