import pygame
import socket
import threading
import time

from connection_handler import ConnectionHandler
from input_handler import KeyboardInputHandler

from tile import Tile
from ball import BallDummy, BallShadow

from pygame.locals import *


class Game():
    def __init__(self, network, name, input_handler):
        self.network = network
        self.network.game = self

        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720), 0, 32)

        pygame.display.set_caption("It's Super Cool!")
        pygame.display.set_icon(pygame.image.load('assets/meteorFullRound_SW.png'))

        self.surface = pygame.Surface(self.screen.get_size())
        self.surface = self.surface.convert_alpha()
        self.screen.blit(self.surface, (0, 0))
        self.font_big = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 20)

        self.players = []
        self.input_handlers = []
        self.heroes = []
        self.ball = BallDummy()
        self.ball_shadow = BallShadow(self.ball)

        self.background_sprites = pygame.sprite.Group()
        self.clock = pygame.time.Clock()

        self.load_map()
        threading.Thread(target=network.handle).start()
        self.network.join(name, input_handler)

    def run(self):
        while True:
            self.input()
            delta = self.clock.tick(60) / 1000

            self.background_sprites.draw(self.screen)

            self.surface.fill((255, 255, 255))
            text = self.font_big.render("It's Super Cool!", 1, (255, 255, 255))
            text2 = self.font_big.render("It's Super Cool!", 1, (0, 0, 0))
            textpos = text.get_rect()
            textpos.centerx = 640
            textpos.centery = 360
            textpos2 = text2.get_rect()
            textpos2.centerx = 640
            textpos2.centery = 362
            self.screen.blit(text2, textpos2)
            self.screen.blit(text, textpos)

            self.ball.update(delta)
            self.ball_shadow.update()

            for hero in self.heroes:
                hero.update(delta)

                if hero.throws:
                    power = min(2, time.time() - hero.hold) / 2
                    pygame.draw.rect(self.screen, (0, 0, 0),
                                     (hero.rect.centerx - 25, hero.rect.centery - 10 - 25, 50, 20))
                    pygame.draw.rect(self.screen, (255, 255, 255),
                                     (hero.rect.centerx - 25, hero.rect.centery - 10 - 25, 50 * power, 20))

            for input_handler in self.input_handlers:
                hero = input_handler.hero
                self.network.send({
                    'operation': 'move',
                    'x': hero.position.x,
                    'y': hero.position.y,
                    'z': hero.position.z,
                    'vel_x': hero.movement.x,
                    'vel_y': hero.movement.y,
                    'vel_z': hero.movement.z,
                })

            action_sprites = pygame.sprite.Group()
            action_sprites.add(self.ball_shadow)
            action_sprites.add(self.heroes)
            action_sprites.add(self.ball)
            action_sprites.draw(self.screen)

            pygame.display.flip()
            pygame.display.update()

    def get_hero(self, id):
        for hero in self.heroes:
            if hero.id == id:
                return hero
        return None

    def input(self):
        for event in pygame.event.get():
            for input_handler in self.input_handlers:
                if input_handler.handle(event):  # Handler did handle it
                    break

    def load_map(self):
        for x in range(20):
            for y in range(20):
                tile = Tile()
                tile.rect.centerx = x * 75 - 75
                tile.rect.centery = y * 53 - 53
                self.background_sprites.add(tile)

        map = pygame.sprite.Sprite()
        map.image = pygame.transform.scale(pygame.image.load("map.png").convert_alpha(), (1302, 1146))
        map.rect = map.image.get_rect()
        map.rect.x = 0
        map.rect.y = -200

        self.background_sprites.add(map)


def connect(address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((address, 9525))
    return ConnectionHandler(sock)


if __name__ == '__main__':
    # Todo: uncomment
    # address = input('Server address please (leave empty for localhost):')
    # if len(address) == 0:
    #    address = 'localhost'
    #
    # handler = connect(address)
    handler = connect('localhost')

    print('Connected')

    time.sleep(1)

    # configs = [('Kamil', KeyboardInputHandler('wasd'))]

    game = Game(handler, 'Mati', KeyboardInputHandler('wasdjk'))
    game.run()