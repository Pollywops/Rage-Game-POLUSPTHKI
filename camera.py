import pygame

class Camera:
    def __init__(self, screen_size):
        self.resize(screen_size)
        self.offset = pygame.Vector2(0, 0)

    def resize(self, screen_size):
        self.screen_w, self.screen_h = screen_size

    def update(self, target_rect):
        self.offset.x = target_rect.centerx - self.screen_w / 2
        self.offset.y = target_rect.centery - self.screen_h / 2

    def apply_rect(self, rect):
        return rect.move(-self.offset.x, -self.offset.y)
