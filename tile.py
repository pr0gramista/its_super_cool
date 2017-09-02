import pygame

class Tile(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("assets/groundTile_NE.png").convert_alpha()
        self.rect = self.image.get_rect()