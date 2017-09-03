#
# It's Super Cool
#
# Assets by Kenney (https://kenney.nl/)
# Some sounds effects came from freeSFX (http://www.freesfx.co.uk)

import pygame
import socket
import threading
import time
import settings
import random
import sys

from connection_handler import ConnectionHandler
from input_handler import KeyboardInputHandler

from tile import Tile, Gate, ConsoleTop, ConsoleBottom, Spectator
from ball import BallDummy, BallShadow

from vector import Vector


class Game():
    def is_local_player_id(self, id):
        return id in self.local_players

    def __init__(self, players_to_call):
        self.running = False

        self.local_players = []

        pygame.init()

        self.screen = pygame.display.set_mode((settings.RESOLUTION_X, settings.RESOLUTION_Y), pygame.RESIZABLE)

        self.canvas_width = 1280
        self.canvas_height = 720
        self.screen_width = settings.RESOLUTION_X
        self.screen_height = settings.RESOLUTION_Y

        pygame.display.set_caption("It's Super Cool!")
        pygame.display.set_icon(pygame.image.load('assets/icon.png'))

        self.canvas = pygame.Surface((self.canvas_width, self.canvas_height))
        self.canvas_scaled = None

        self.surface = pygame.Surface((self.canvas_width, self.canvas_height))
        self.surface = self.surface.convert_alpha()
        self.screen.blit(self.surface, (0, 0))
        self.font_big = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 20)

        self.sounds = {}
        self.input_handlers = []
        self.heroes = []
        self.ball = BallDummy()
        self.ball_shadow = BallShadow(self.ball)
        self.main_sprites = []
        self.spectators = []

        self.background_sprites = pygame.sprite.Group()
        self.clock = pygame.time.Clock()

        self.points_astronauts = 0
        self.points_aliens = 0
        self.action_sprites = pygame.sprite.Group()

        self.load_map()
        self.load_sounds()

        for player_to_call in players_to_call:
            player_to_call['network'].game = self
            networking_thread = threading.Thread(target=player_to_call['network'].handle)
            networking_thread.daemon = True
            networking_thread.start()
            player_to_call['network'].join(player_to_call['name'], player_to_call['input_handler'], player_to_call['team'])

        self.play_sound('cheer', loops=-1)

    def run(self):
        self.running = True
        first_run_time = time.time()
        while True:
            self.input()
            delta = self.clock.tick(60) / 1000

            self.background_sprites.draw(self.canvas)

            points_text = "Astronauts {}:{} Aliens".format(self.points_astronauts, self.points_aliens)
            points_display = self.font_big.render(points_text, 1, (255, 255, 255))
            points_display_shadow = self.font_big.render(points_text, 1, (0, 0, 0))
            points_display_rect = points_display.get_rect()
            points_display_rect.centerx = self.canvas_width / 2
            points_display_rect.centery = 50
            points_display_shadow_rect = points_display_shadow.get_rect()
            points_display_shadow_rect.centerx = self.canvas_width / 2
            points_display_shadow_rect.centery = 52
            self.canvas.blit(points_display_shadow, points_display_shadow_rect)
            self.canvas.blit(points_display, points_display_rect)

            self.ball.update(delta)
            self.ball_shadow.update()

            for spectator in self.spectators:
                spectator.check_timer()

            for hero in self.heroes:
                hero.update(delta)

                if hero.throws:
                    power = min(2, time.time() - hero.hold) / 2
                    pygame.draw.rect(self.canvas, (0, 0, 0),
                                     (hero.rect.centerx - 25, hero.rect.centery - 10 - 25, 50, 10))
                    pygame.draw.rect(self.canvas, (255, 255, 255),
                                     (hero.rect.centerx - 25, hero.rect.centery - 10 - 25, 50 * power, 10))

            for input_handler in self.input_handlers:
                if input_handler.hero is not None:
                    hero = input_handler.hero
                    hero.update_pos()

            sprites_to_draw = self.main_sprites.copy()
            sprites_to_draw.append(self.ball)
            sprites_to_draw += self.heroes

            sprites_to_draw = sorted(sprites_to_draw, key=lambda s: - (s.position.y - s.rect.height * 0.00925925))

            self.action_sprites.empty()
            for s in sprites_to_draw:
                if s is self.ball:
                    self.action_sprites.add(self.ball_shadow)
                self.action_sprites.add(s)
            self.action_sprites.add(self.console_bottom)
            self.action_sprites.draw(self.canvas)

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
                self.canvas.blit(text2, textpos2)
                self.canvas.blit(text, textpos)

            # Final draw
            self.screen.fill((0, 0, 0))
            if self.canvas_width == self.screen_width and self.canvas_height == self.screen_height:
                self.screen.blit(self.canvas, (0, 0))
            else:
                scaled_size = self.canvas_scaled.get_size()
                scaled_width = scaled_size[0]
                scaled_height = scaled_size[1]

                if settings.QUALITY_SCALING:
                    pygame.transform.smoothscale(self.canvas, (scaled_width, scaled_height), self.canvas_scaled)
                else:
                    pygame.transform.scale(self.canvas, (scaled_width, scaled_height), self.canvas_scaled)
                self.screen.blit(self.canvas_scaled,
                                 ((self.screen_width - scaled_width) / 2, (self.screen_height - scaled_height) / 2))

            pygame.display.flip()
            pygame.display.update()

    def get_hero(self, id):
        for hero in self.heroes:
            if hero.id == id:
                return hero
        return None

    def input(self):
        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                self.screen_width = event.w
                self.screen_height = event.h

                a = self.screen_width / self.canvas_width
                b = self.screen_height / self.canvas_height

                scaled_width = 0
                scaled_height = 0
                if self.canvas_height * a < self.screen_height:
                    scaled_width = self.canvas_width * a
                    scaled_height = self.canvas_height * a
                else:
                    scaled_width = self.canvas_width * b
                    scaled_height = self.canvas_height * b

                scaled_width = round(scaled_width)
                scaled_height = round(scaled_height)

                self.canvas_scaled = pygame.Surface((scaled_width, scaled_height))
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            else:
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
        map.image = pygame.transform.scale(pygame.image.load("assets/map.png").convert_alpha(), (1302, 1146))
        map.rect = map.image.get_rect()
        map.rect.x = 0
        map.rect.y = -200

        self.background_sprites.add(map)
        self.background_sprites.add(ConsoleTop())

        self.console_bottom = ConsoleBottom()

        for i in range(1, 7):
            gate = Gate(i)
            self.main_sprites.append(gate)

        for i in range(random.randint(10, 30)):
            x = (-0.6, -1.8)
            y = (-0.2, 5.2)
            spectator = Spectator('SE', Vector(x[0] + random.random() * x[1], y[0] + random.random() * y[1], 0))
            self.spectators.append(spectator)
            self.background_sprites.add(spectator)

        for i in range(random.randint(5, 15)):
            x = (-0.4, 2.8)
            y = (-1.0, -0.4)
            spectator = Spectator('NE', Vector(x[0] + random.random() * x[1], y[0] + random.random() * y[1], 0))
            self.spectators.append(spectator)
            self.background_sprites.add(spectator)

        for i in range(random.randint(10, 30)):
            x = (2.8, 0.4)
            y = (-0.6, 5.4)
            spectator = Spectator('NW', Vector(x[0] + random.random() * x[1], y[0] + random.random() * y[1], 0))
            self.spectators.append(spectator)
            self.background_sprites.add(spectator)

        for i in range(random.randint(10, 15)):
            x = (-0.2, 2.4)
            y = (5.4, 1.2)
            spectator = Spectator('SW', Vector(x[0] + random.random() * x[1], y[0] + random.random() * y[1], 0))
            self.spectators.append(spectator)
            self.background_sprites.add(spectator)

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
    address = 'localhost'
    if len(settings.SERVER) > 0:
        print('Connecting to server address from settings')
        address = settings.SERVER
    else:
        address = input('Server address please (leave empty for localhost):')
        if len(address) == 0:
            address = 'localhost'

    nickname = settings.NICKNAME
    if len(nickname) > 0:
        print('Nickname loaded from settings')
    else:
        nickname = input('Type in your nickname (edit your settings to avoid this step):')

    handler = connect(address)

    team_str = input('Team (0 - for astronauts, 1 - for aliens)')
    team = int(team_str)
    if team > 1 or team < 0:
        sys.exit()

    print('Connected to {}'.format(address))

    players_to_call = []
    players_to_call.append({
        'network': handler,
        'name': nickname,
        'input_handler': KeyboardInputHandler(settings.KEYBOARD_MAPPING),
        'team': team
    })

    # Run additional players
    for i in range(2, 5):
        try:
            player_settings = getattr(settings, 'PLAYER_{}'.format(i))
            if player_settings is not None:
                handler_2 = connect(address)
                players_to_call.append({
                    'network': handler_2,
                    'name': player_settings[0],
                    'input_handler': KeyboardInputHandler(player_settings[1]),
                    'team': player_settings[2]
                })
        except AttributeError:
            pass

    game = Game(players_to_call)
    game.run()
