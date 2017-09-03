import pygame
import settings

__map_x_min = -0.22
__map_x_max = 2.0
__map_y_min = -0.37
__max_y_max = 4.8


def get_position(x, y, z):
    global camera_x, camera_y
    pox = (x + y) * 75 + 360
    poy = (x - y) * 54 + 415 + (-54 * z)  # Invert z
    return (pox, poy)


def load_image(path, scale):
    image = pygame.image.load(path).convert_alpha()
    rect = image.get_rect()
    return pygame.transform.scale(image, (round(rect.width * scale), round(rect.height * scale)))


def cut_to_map(x, y, z):
    return (max(min(x, __map_x_max), __map_x_min), max(min(y, __max_y_max), __map_y_min), max(z, 0))


def bounce_to_map(x, y, z):
    bounce_x = 1
    bounce_y = 1
    bounce_z = 1
    bounce_ratio = -1 * settings.BOUNCE_RATIO

    if x < __map_x_min:
        bounce_x = bounce_ratio
    elif x > __map_x_max:
        bounce_x = bounce_ratio

    if y < __map_y_min:
        bounce_y = bounce_ratio
    elif y > __max_y_max:
        bounce_y = bounce_ratio

    if z < 0:
        bounce_z = bounce_ratio * 0.5

    return bounce_x, bounce_y, bounce_z
