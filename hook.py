import pygame

class Hook(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.surface = pygame.surface.Surface((10, 10))
        self.surface.fill((255,255,0))
        self.rect = self.surface.get_rect()
        self.hooking = False
    def update(self, gun, blocks):
        self.rect.centerx, self.rect.centery = gun.rect.center
        self.vx, self.vy = gun.vx, gun.vy
        self.transformed_image = pygame.transform.rotate(self.surface, gun.deg)
        if self.hooking:
            for sprite in pygame.sprite.spritecollide(self, blocks, False):
                if self.rect.colliderect(sprite.rect):
                    self.hooking = False


    def hook(self):
        self.rect.centerx += self.vx
        self.rect.centery += self.vy
        self.hooking = True

    def draw(self, screen, cam):
        screen.blit(self.transformed_image, cam.apply_rect(self.rect))