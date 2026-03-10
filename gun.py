import pygame, math

# Checkt of er al geluid is
# Zo niet dan wordt het gestart
if not pygame.mixer.get_init():
    pygame.mixer.init()

# Geluids effecten
shotgun_shot = pygame.mixer.Sound('sounds/Shotgun_shot.mp3')
shotgun_shot.set_volume(0.03)
shotgun_empty = pygame.mixer.Sound('sounds/Empty.mp3')
shotgun_empty.set_volume(.03)

# Kracht op basis van kogel
BULLET_STRENGTH = {
    "NORMAL": 1.15,
    "SUPER": 1.6
}

class Gun(pygame.sprite.Sprite):
    def __init__(self, w, h):
        super().__init__()
        # Afbeeldng shotgun wordt geladen
        self.realimage = pygame.image.load('textures/Shotgun.png').convert_alpha()
        # Afbeelding van de shotgun wordt nar 64x64 pixels geschaald
        self.original_image = pygame.transform.scale(self.realimage, (64, 64))
        # Afbeelding wordt steeds aangepast bij het draaien
        self.image = self.original_image
        # Rect voor positie
        self.rect = self.image.get_rect()
        self.rect.center = (10, 10)
        # Of de shotgun gespiegeld is
        self.flipped = False
        # Aantal kogels in het begin
        self.bullets = 2
        # Start type kogel
        self.bullet_type = 'NORMAL'
        self.super_shots_left = 0

    def activate_super_shots(self, amount=2):
        self.bullet_type = 'SUPER'
        self.super_shots_left = amount
        self.bullets = amount


    def shoot(self, player):

        # Haalt de Kracht uit de Type kogel
        self.bullet_strength = BULLET_STRENGTH[self.bullet_type]

        # Kijkt of er meer dan 1 Kogel is
        if self.bullets:

            # Haalt Na elk shot een kogel eraf
            self.bullets -= 1
            # Speelt het schiet geluid af
            shotgun_shot.play()

            #Checkt of het wapen niet recht naar boven wijst
            if not (40 < self.deg < 140):

                # Als speler naar beneden vlt
                if player.vely > 0:
                    # Stopt neerwaarste snelheid
                    player.vely = 0
                    #print(player.vely)

            # Berkent de recoil
            # Stuurt de speler de andere kant op
            addvelx = -math.cos(self.angle) * 6.5 * self.bullet_strength
            addvely = -math.sin(self.angle) * 6.5 * self.bullet_strength

            # Voeg velocity toe aan speler
            player.add_vel(addvelx, addvely)

            if self.bullet_type == 'SUPER':
                self.super_shots_left -= 1
                if self.super_shots_left <= 0:
                    self.bullet_type = 'NORMAL'
                    self.super_shots_left = 0
        else:
            # Als shotgun leeg is dan speelt het lege geluid af
            shotgun_empty.play()

    def update(self, player, cam):
        # Haalt de muispositie op
        mx,my = cam.apply_mouse()
        # Berkend de hoek tussen de speler en de muis
        self.angle = math.atan2(my - player.rect.centery, mx - player.rect.centerx)
        # print(f'x:{math.cos(self.angle)}, y:{math.sin(self.angle)}')
        # Zorgt dat het wapen altijd 80 pixels van de speler blijft
        self.vx, self.vy = (player.rect.centerx + math.cos(self.angle) * 40),(player.rect.centery + math.sin(self.angle) * 40)
        self.pos = (self.vx, self.vy)
        # Hoek in graden
        self.deg = -math.degrees(self.angle)
        # Als het wapen naar links wijst dan wordt de afbelding gespiegeld
        if abs(self.deg) > 90 and not self.flipped:
            self.original_image = pygame.transform.flip(self.original_image, False, True)
            self.flipped = True
        # Als het wapen naar rechts wijst dan wordt de afbeelding terug gespiegeld
        elif (-90 <= self.deg <= 90) and self.flipped:
            self.original_image = pygame.transform.flip(self.original_image, False, True)
            self.flipped = False

            # print(deg)
            # print(self.flipped)
    def draw(self, screen, cam):
        # Roteer de afbeelding naar de jiuste hoek
        self.image = pygame.transform.rotate(self.original_image, self.deg)
        # Maak nieuwe rect op basis van geroteerde image
        self.rect = self.image.get_rect(center=self.pos)
        # Tekent het wapen opnieuw
        screen.blit(self.image, cam.apply_rect(self.rect))
