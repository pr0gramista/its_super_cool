import pygame
import sys
import time

from pygame.locals import *


class InputHandler():
    def __init__(self):
        self.game = None
        self.hero = None
        self.connection_handler = None

        self.id = 0

    def handle(self, event):
        if event.type == QUIT:
            pygame.quit()
            sys.exit()


class KeyboardInputHandler(InputHandler):
    def __init__(self, keys='wasdjk'):
        keys = keys.lower()
        if len(keys) == 6:
            self.UP = ord(keys[0])
            self.LEFT = ord(keys[1])
            self.DOWN = ord(keys[2])
            self.RIGHT = ord(keys[3])
            self.ACTION_1 = ord(keys[4])
            self.ACTION_2 = ord(keys[5])
        else:
            print('Keyboard input handler not set correctly (missing exactly 4 keys)')

        self.throws = False

    def handle(self, event):
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == self.UP:
                self.hero.move_up()
            elif event.key == self.DOWN:
                self.hero.move_down()
            elif event.key == self.RIGHT:
                self.hero.move_right()
            elif event.key == self.LEFT:
                self.hero.move_left()
            elif event.key == self.ACTION_1:
                if self.game.ball.grabbed and self.game.ball.grabbed_by == self.hero:
                    self.hero.hold = time.time()
                    self.hero.throws = True
                    self.hero.throwing()
                elif self.game.ball.grabbed == False:
                    self.hero.grab()
        elif event.type == KEYUP:
            if event.key == self.UP:
                self.hero.move_up(stop=True)
            elif event.key == self.DOWN:
                self.hero.move_down(stop=True)
            elif event.key == self.RIGHT:
                self.hero.move_right(stop=True)
            elif event.key == self.LEFT:
                self.hero.move_left(stop=True)
            elif event.key == self.ACTION_1:
                if self.hero.throws:
                    self.hero.throws = False
                    # Power is calculated a load for 2 seconds, must be in (0, 1)
                    self.hero.throw(min(2, time.time() - self.hero.hold) / 2)
