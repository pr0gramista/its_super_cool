import pygame
import socket
import threading
import time

from connection_handler import ConnectionHandler
from input_handler import KeyboardInputHandler

from tile import Tile
from ball import BallDummy, BallShadow


class Game():
    def __init__(self, network, name, input_handler):
        self.network = network
        self.network.game = self

        pygame.init()
        self.SCREEN_WIDTH = 1280
        self.SCREEN_HEIGHT = 720
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), 0, 32)

        pygame.display.set_caption("It's Super Cool!")
        pygame.display.set_icon(pygame.image.load('assets/icon.png'))

        self.surface = pygame.Surface(self.screen.get_size())
        self.surface = self.surface.convert_alpha()
        self.screen.blit(self.surface, (0, 0))
        self.font_big = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 20)

        self.sounds = {}
        self.players = []
        self.input_handlers = []
        self.heroes = []
        self.ball = BallDummy()
        self.ball_shadow = BallShadow(self.ball)

        self.background_sprites = pygame.sprite.Group()
        self.clock = pygame.time.Clock()

        self.points_astronauts = 0
        self.points_aliens = 0

        self.load_map()
        self.load_sounds()

        threading.Thread(target=network.handle).start()
        self.network.join(name, input_handler)

        self.play_sound('cheer', loops=-1)

    def run(self):
        first_run_time = time.time()
        while True:
            self.input()
            delta = self.clock.tick(60) / 1000

            self.background_sprites.draw(self.screen)

            points_text = "Astronauts {}:{} Aliens".format(self.points_astronauts, self.points_aliens)
            points_display = self.font_big.render(points_text, 1, (255, 255, 255))
            points_display_shadow = self.font_big.render(points_text, 1, (0, 0, 0))
            points_display_rect = points_display.get_rect()
            points_display_rect.centerx = self.SCREEN_WIDTH / 2
            points_display_rect.centery = 50
            points_display_shadow_rect = points_display_shadow.get_rect()
            points_display_shadow_rect.centerx = self.SCREEN_WIDTH / 2
            points_display_shadow_rect.centery = 52
            self.screen.blit(points_display_shadow, points_display_shadow_rect)
            self.screen.blit(points_display, points_display_rect)

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

            if time.time() - 3 < first_run_time:
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

    def load_sounds(self):
        self.sounds['hit'] = pygame.mixer.Sound('sounds/hit.ogg')
        self.sounds['hit2'] = pygame.mixer.Sound('sounds/hit2.ogg')
        self.sounds['swish'] = pygame.mixer.Sound('sounds/swish.ogg')
        self.sounds['stun'] = pygame.mixer.Sound('sounds/stun.ogg')
        self.sounds['bounce'] = pygame.mixer.Sound('sounds/bounce.ogg')
        self.sounds['cheer'] = pygame.mixer.Sound('sounds/cheer.ogg')
        self.sounds['goal'] = pygame.mixer.Sound('sounds/goal.ogg')

        for sound in self.sounds.values():
            sound.set_volume(0.5)
        self.sounds['cheer'].set_volume(0.10)

    def play_sound(self, sound, loops=0):
        self.sounds[sound].play(loops)


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
