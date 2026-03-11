import pygame, math

class HProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, angle, speed):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.rect = self.image.get_rect()
        self.image.fill((0, 0, 0))
        self.pos = pygame.Vector2(x, y)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.angle = angle
        self.speed = 30
        self.ancored = False

    def update(self, blocks, player, cam, screen):
        if not self.ancored:
            self.pos.x += math.cos(self.angle) * self.speed
            self.pos.y += math.sin(self.angle) * self.speed
            self.rect.center = (round(self.pos.x), round(self.pos.y))

            for i in blocks.sprites():
                if self.rect.colliderect(i.rect):
                    self.ancored = True
                    player.rope(self.rect.center)
                    break

        start = pygame.Vector2(cam.apply_rect(player.rect).center)
        end = pygame.Vector2(cam.apply_rect(self.rect).center)
        pygame.draw.line(screen, (0, 0, 0), start, end, 3)

    def draw(self, screen, cam):
        screen.blit(self.image, cam.apply_rect(self.rect))