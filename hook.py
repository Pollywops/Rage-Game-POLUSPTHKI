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
        self.angle = gun.angle
        self.transformed_image = pygame.transform.rotate(self.surface, gun.deg)
        if self.hooking:
            self.pro.update()
    def hook(self, projectile):
        self.pro = projectile.start(self.rect.centerx, self.rect.centery, 10 ,10, self.angle, 1)
        self.hooking = True
    def draw(self, screen, cam):
        screen.blit(self.transformed_image, cam.apply_rect(self.rect))
        if self.hooking:
            self.pro.draw(screen, cam)