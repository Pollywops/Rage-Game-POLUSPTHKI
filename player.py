import pygame
import os

BASE_DIR = os.path.dirname(__file__)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, color):
        super().__init__()
        self.realimage = pygame.image.load(os.path.join(BASE_DIR, 'textures', 'Pot.png')).convert_alpha()
        self.originalimage = pygame.transform.scale(self.realimage, (60, 60))
        self.image = self.originalimage
        self.rect = self.image.get_rect()
        self.rect.center = x, y

        self.centerx = x
        self.centery = y
        self.velx = 0
        self.vely = 0
        self.touchingground = False
        self.wasgrounded = False
        self.touchingwall = False
        self.touchingceiling = False
        self.friction = 1

    def add_vel(self, x, y):
        self.velx += x
        self.vely += y

    def physics(self, blocks, gun):
        self.touchingground = False
        self.touchingwall = False
        self.touchingceiling = False

        self.vely += 0.4
        self.friction = 1

        self.rect.centerx += self.velx
        for sprite in pygame.sprite.spritecollide(self, blocks, False):
            if self.rect.colliderect(sprite.rect):
                if self.velx > 0:
                    self.rect.right = sprite.rect.left
                    self.velx = 0
                elif self.velx < 0:
                    self.rect.left = sprite.rect.right
                    self.velx = 0
            gun.bullets = 2
        self.rect.centery += self.vely
        for sprite in pygame.sprite.spritecollide(self, blocks, False):
            if self.rect.colliderect(sprite.rect):
                if self.vely > 0:
                    self.rect.bottom = sprite.rect.top
                    self.vely = 0
                    self.touchingground = True
                    self.friction = 30
                    # print(self.friction)
                elif self.vely < 0:
                    self.rect.top = sprite.rect.bottom
                    self.vely = 0
                    self.touchingceiling = True
                    self.friction = 30
            gun.bullets = 2

        if self.velx > 0:
            if self.velx <= 0.005:
                self.velx = 0

            else:
                self.velx -= 0.03 * self.friction
                if self.velx <= 0.03:
                    self.velx = 0
        if self.velx < 0:
            if self.velx >= 0.005:
                self.velx = 0

            else:
                self.velx += 0.03 * self.friction
                if self.velx >= 0.03:
                    self.velx = 0

    def update(self, blocks, gun):
        self.physics(blocks, gun)

    def draw(self, screen, cam):
        screen.blit(self.image, cam.apply_rect(self.rect))
    