import pygame, math

class HProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, angle, speed):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect()

        self.pos = pygame.Vector2(x, y)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.angle = angle
        self.speed = speed
        self.ancored = False
        self.broken = False

    def update(self, blocks, player, cam, screen):
        if self.broken:
            return

        if not self.ancored:
            move = pygame.Vector2(math.cos(self.angle), math.sin(self.angle)) * self.speed

            # kleine stapjes zodat hij niet door blocks heen gaat schiet
            steps = int(self.speed)
            step_move = move / steps

            for _ in range(steps):
                self.pos += step_move
                self.rect.center = (round(self.pos.x), round(self.pos.y))

                for i in blocks.sprites():
                    if not self.rect.colliderect(i.rect):
                        continue

                    # als hij een slime aanraakt moet hij meteen breken
                    if getattr(i, "bouncy", False):
                        player.derope()
                        self.broken = True
                        return

                    # als hij een normaal blok raakt hangt hij gewoon
                    self.ancored = True
                    player.rope(self.rect.center)
                    return

        start = pygame.Vector2(cam.apply_rect(player.rect).center)
        end = pygame.Vector2(cam.apply_rect(self.rect).center)
        pygame.draw.line(screen, (255, 255, 255), start, end, 3)

    def draw(self, screen, cam):
        if not self.broken:
            screen.blit(self.image, cam.apply_rect(self.rect))