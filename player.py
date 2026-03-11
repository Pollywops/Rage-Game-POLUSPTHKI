import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, color):
        super().__init__()
        self.realimage = pygame.image.load('textures/Pot.png').convert_alpha()
        self.originalimage = pygame.transform.scale(self.realimage, (32, 32))
        self.image = self.originalimage
        self.rect = self.image.get_rect()

        self.hooked = False
        self.anchor = pygame.Vector2(0, 0)
        self.rope_len = 0.0

        self.rect.center = x, y
        self.start_pos = (x, y)

        self.pos = pygame.Vector2(x, y)
        self.centerx = x
        self.centery = y

        self.velx = 0
        self.vely = 0

        self.touchingground = False
        self.wasgrounded = False
        self.touchingceiling = False

        self.friction = 1

    def add_vel(self, x, y):
        self.velx += x
        self.vely += y

    def fix_colx(self, blocks):
        self.pos.x += self.velx
        self.rect.centerx = round(self.pos.x)

        for sprite in pygame.sprite.spritecollide(self, blocks, False):
            if self.rect.colliderect(sprite.rect):
                if self.velx > 0:
                    self.rect.right = sprite.rect.left
                    self.pos.x = self.rect.centerx
                    self.velx = 0
                elif self.velx < 0:
                    self.rect.left = sprite.rect.right
                    self.pos.x = self.rect.centerx
                    self.velx = 0

    def fix_coly(self, blocks):
        self.pos.y += self.vely
        self.rect.centery = round(self.pos.y)

        for sprite in pygame.sprite.spritecollide(self, blocks, False):
            if self.rect.colliderect(sprite.rect):
                if self.vely > 0:
                    self.rect.bottom = sprite.rect.top
                    self.pos.y = self.rect.centery
                    self.vely = 0
                elif self.vely < 0:
                    self.rect.top = sprite.rect.bottom
                    self.pos.y = self.rect.centery
                    self.vely = 0

    def rope(self, anchor_pos):
        self.hooked = True
        self.anchor.update(anchor_pos)
        self.rope_len = (self.pos - self.anchor).length()

    def derope(self):
        self.hooked = False

    def apply_rope_tens(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.rope_len = max(40, self.rope_len - 3)

        if keys[pygame.K_s]:
            self.rope_len += 3

        if not self.hooked:
            return

        d = self.pos - self.anchor
        dist = d.length()

        if dist <= 0.0001:
            return

        if dist > self.rope_len:
            norm = d / dist

            # zet speler exact terug op de touwcirkel
            self.pos = self.anchor + norm * self.rope_len

            # haal snelheid weg in de richting van het touw
            v_radial = self.velx * norm.x + self.vely * norm.y
            if v_radial > 0:
                self.velx -= v_radial * norm.x
                self.vely -= v_radial * norm.y

            # klein beetje demping tegen energie-opbouw
            self.velx *= 0.995
            self.vely *= 0.995

            self.rect.center = (round(self.pos.x), round(self.pos.y))

    def physics(self, blocks, gun):
        self.touchingground = False
        self.touchingceiling = False
        self.friction = 1

        self.vely += 0.4

        # X-beweging
        old_rect = self.rect.copy()
        self.pos.x += self.velx
        self.rect.centerx = round(self.pos.x)

        for sprite in pygame.sprite.spritecollide(self, blocks, False):
            if sprite.info.get("spike", False) or sprite.info.get("super_pickup", False):
                continue

            if self.rect.colliderect(sprite.rect):
                self.friction = sprite.friction

                if sprite.info.get("bouncy", False):
                    if old_rect.right <= sprite.rect.left and self.velx > 0:
                        self.rect.right = sprite.rect.left
                        self.pos.x = self.rect.centerx
                        self.velx = -abs(self.velx)
                    elif old_rect.left >= sprite.rect.right and self.velx < 0:
                        self.rect.left = sprite.rect.right
                        self.pos.x = self.rect.centerx
                        self.velx = abs(self.velx)
                else:
                    if self.velx > 0:
                        self.rect.right = sprite.rect.left
                        self.pos.x = self.rect.centerx
                        self.velx = 0
                    elif self.velx < 0:
                        self.rect.left = sprite.rect.right
                        self.pos.x = self.rect.centerx
                        self.velx = 0

                gun.bullets = 2

        # Y-beweging
        old_rect = self.rect.copy()
        self.pos.y += self.vely
        self.rect.centery = round(self.pos.y)

        for sprite in pygame.sprite.spritecollide(self, blocks, False):
            if sprite.info.get("spike", False) or sprite.info.get("super_pickup", False):
                continue

            if self.rect.colliderect(sprite.rect):
                self.friction = sprite.friction

                if sprite.info.get("bouncy", False):
                    if old_rect.bottom <= sprite.rect.top and self.vely > 0:
                        self.rect.bottom = sprite.rect.top
                        self.pos.y = self.rect.centery
                        self.vely = -abs(self.vely) * 0.9
                        self.touchingground = True
                    elif old_rect.top >= sprite.rect.bottom and self.vely < 0:
                        self.rect.top = sprite.rect.bottom
                        self.pos.y = self.rect.centery
                        self.vely = abs(self.vely) * 0.9
                        self.touchingceiling = True
                else:
                    if self.vely > 0:
                        self.rect.bottom = sprite.rect.top
                        self.pos.y = self.rect.centery
                        self.vely = 0
                        self.touchingground = True
                    elif self.vely < 0:
                        self.rect.top = sprite.rect.bottom
                        self.pos.y = self.rect.centery
                        self.vely = 0
                        self.touchingceiling = True

                gun.bullets = 2

        if self.velx > 0:
            self.velx -= 0.03 * self.friction
            if self.velx < 0:
                self.velx = 0
        elif self.velx < 0:
            self.velx += 0.03 * self.friction
            if self.velx > 0:
                self.velx = 0

        self.apply_rope_tens()
        self.rect.center = (round(self.pos.x), round(self.pos.y))
    def update(self, blocks, gun):
        self.physics(blocks, gun)

    def draw(self, screen, cam):
        screen.blit(self.image, cam.apply_rect(self.rect))

    def reset_position(self):
        self.pos.x = self.start_pos[0]
        self.pos.y = self.start_pos[1]
        self.rect.center = self.start_pos
        self.hooked = False
        self.velx = 0
        self.vely = 0