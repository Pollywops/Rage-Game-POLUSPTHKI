import pygame

class Camera:
    def __init__(self, screen_size):
        # Constructor van de camera
        # screen_size (breedte, hoogte)

        self.resize(screen_size) # Stel de schermbreedte en schermhoogte in
        self.offset = pygame.Vector2(0, 0) # Hoe veel de camera is bewogen in de wereld

    def resize(self, screen_size):
        self.screen_w, self.screen_h = screen_size
        # Wordt gebruikt als het schermgrootte verandert
        # Slaat de nieuwe schermbreedte en schermhoogte op

    def update_center(self, target_rect):
        # Zorgt dat de camera bij de speler blijft

        self.offset.x = target_rect.centerx - self.screen_w / 2
        self.offset.y = target_rect.centery - self.screen_h / 2
        # Berekent hoeveel de camera moet verschuiven

    def apply_rect(self, rect):
        # Past een rect aan op basis van de camera offset
        # Hiermee tekent de speler op de juiste plek op het scherm

        return rect.move(-self.offset.x, -self.offset.y)

    def apply_mouse(self):
        # Zet de muispositie om naar wereldpositie
        return pygame.math.Vector2(pygame.mouse.get_pos()[0] + self.offset.x, pygame.mouse.get_pos()[1] + self.offset.y)
