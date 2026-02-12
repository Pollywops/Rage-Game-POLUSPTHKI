import pygame, math

if pygame.mixer.get_init() == None:
    pygame.mixer.init()
shotgun_shot = pygame.mixer.Sound('sounds/Shotgun_shot.mp3')
shotgun_empty = pygame.mixer.Sound('sounds/Empty.mp3')

class Gun(pygame.sprite.Sprite):
    def __init__(self, w, h):
        super().__init__()
        self.realimage = pygame.image.load('textures/Shotgun.png').convert_alpha()
        self.original_image = pygame.transform.scale(self.realimage, (128, 128))
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.center = (10, 10)
        self.flipped = False
        self.bullets = 2
        self.bullet_type = 'NORMAL'
        self.bullet_strength = 1

    def shoot(self, player):

        if self.bullet_type == 'NORMAL':
            self.bullet_strength = 1
        elif self.bullet_type == 'SUPER':
            self.bullet_strength = 1.5
        if self.bullets > 0:
            self.bullets = self.bullets - 1
            shotgun_shot.play()
            if not(self.deg > 40 and self.deg < 140):
                if player.vely > 0:
                    player.vely = 0
                    print(player.vely)
            addvelx = -math.cos(self.angle) * 10 * self.bullet_strength
            addvely = -math.sin(self.angle) * 10 * self.bullet_strength
            player.add_vel(addvelx, addvely)
        else:
            shotgun_empty.play()

    def update(self, player, cam):
        mx,my = cam.apply_mouse()
        self.angle = math.atan2(my - player.rect.centery, mx - player.rect.centerx)
        # print(f'x:{math.cos(self.angle)}, y:{math.sin(self.angle)}')
        self.vx, self.vy = (player.rect.centerx + math.cos(self.angle) * 80),(player.rect.centery + math.sin(self.angle) * 80)
        self.pos = (self.vx, self.vy)
        self.deg = -math.degrees(self.angle)
        if (self.deg < -90 or self.deg > 90) and not self.flipped:
            self.original_image = pygame.transform.flip(self.original_image, False, True)
            self.flipped = True
        elif (-90 <= self.deg <= 90) and self.flipped:
            self.original_image = pygame.transform.flip(self.original_image, False, True)
            self.flipped = False

            # print(deg)
            # print(self.flipped)
    def draw(self, screen, cam):
        self.image = pygame.transform.rotate(self.original_image, self.deg)
        self.rect = self.image.get_rect(center=self.pos)
        screen.blit(self.image, cam.apply_rect(self.rect))