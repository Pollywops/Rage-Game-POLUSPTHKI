import pygame
import random

class Camera:
    def __init__(self, screen_size):
        self.resize(screen_size)
        self.offset = pygame.Vector2(0, 0)
        self.shake_frames = 0
        self.shake_intensity = 0

    def add_shake(self, frames=10, intensity=7):
        self.shake_frames = frames
        self.shake_intensity = intensity

    def update_shake(self):
        if self.shake_frames > 0:
            self.shake_frames -= 1

    def resize(self, screen_size):
        self.screen_w, self.screen_h = screen_size

    def update_center(self, target_rect):
        self.offset.x = target_rect.centerx - self.screen_w / 2 + 200
        self.offset.y = target_rect.centery - self.screen_h / 2

    def apply_rect(self, rect):
        sx, sy = 0, 0
        if self.shake_frames > 0:
            sx = random.randint(-self.shake_intensity, self.shake_intensity)
            sy = random.randint(-self.shake_intensity, self.shake_intensity)
        return rect.move(-self.offset.x + sx, -self.offset.y + sy)


    def apply_mouse(self):
        # Zet de muispositie om naar wereldpositie
        return pygame.math.Vector2(pygame.mouse.get_pos()[0] + self.offset.x, pygame.mouse.get_pos()[1] + self.offset.y)
