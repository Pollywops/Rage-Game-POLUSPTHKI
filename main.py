import pygame,sys
import json
import time
import math
from camera import Camera
from player import Player
from gun import Gun
from hook import Hook
import os
# VARIABLES

pygame.font.init()
pygame.mixer.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PIXELTYPE_PATH = os.path.join(BASE_DIR, "Fonts", "Pixeltype.ttf")
PIXELTYPE_BIG = pygame.font.Font(PIXELTYPE_PATH, 150)
PIXELTYPE_SMALL = pygame.font.Font(PIXELTYPE_PATH, 36)

fontArial = pygame.font.SysFont("Arial", 72)
small_fontArial = pygame.font.SysFont("Arial", 36)

pygame.mixer.set_num_channels(40)
SCREENSIZE = [800,800]
FPS = 60
pygame.font.get_fonts()
state = "menu"

LEVEL_DIR = os.path.join(BASE_DIR, "levels")
os.makedirs(LEVEL_DIR, exist_ok=True)

level_files = sorted([f for f in os.listdir(LEVEL_DIR) if f.lower().endswith(".json")])
selected_level_idx = 0
selected_level_path = os.path.join(LEVEL_DIR, level_files[selected_level_idx]) if level_files else None

##########COLORS##############
RED = (255,0,0)
GREEN = (0,177,64)
BLUE = (30, 144,255)
ORANGE = (252,76,2)
YELLOW = (254,221,0)
PURPLE = (155,38,182)
AQUA = (0,103,127)
WHITE = (200,200,200)
BLACK = (30,30,30)
GRAY = (128,128,128)
##############################


# hier worden de pygame window en clock aangemaakt, en de groepen voor de player, gun, blocks en buttons.
screen = pygame.display.set_mode(SCREENSIZE,flags=pygame.RESIZABLE, vsync=1)
clock = pygame.time.Clock()



player_group = pygame.sprite.GroupSingle()
gun_group = pygame.sprite.GroupSingle()
projectiles = pygame.sprite.Group()
blocks = pygame.sprite.Group()
buttons = pygame.sprite.Group()

# FUNCTIONS

grid_size = 32
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXTURE_DIR = os.path.join(BASE_DIR, "textures")

files = sorted([f for f in os.listdir(TEXTURE_DIR) if f.lower().endswith(".png")])
texture_paths = [os.path.join(TEXTURE_DIR, f) for f in files]

tile_surfaces = [
    pygame.transform.scale(pygame.image.load(p).convert_alpha(), (grid_size, grid_size))
    for p in texture_paths
]


# deze functie zet de lijnen uit het json bestand om in een matrix, zodat deze kan worden gebruikt om de blokken en de player te maken
def load_level_matrix(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("level")
    except:
        return None
EMPTY = 0

def build_blocks_from_matrix(matrix):
    blocks.empty()
    if not matrix:
        return

    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if int(val) == EMPTY:
                continue

            tile_id = int(val) - 1  # <-- belangrijk
            if 0 <= tile_id < len(tile_surfaces):
                blocks.add(Tile(x, y, tile_id))



def draw_menu(screen):
    screen.fill((255, 255, 255))

    title = PIXELTYPE_BIG.render("Rage Game", True, (0, 0, 0))
    hint1 = PIXELTYPE_SMALL.render("ENTER = Play", True, (0, 0, 0))
    hint2 = PIXELTYPE_SMALL.render("ESC = Quit", True, (0, 0, 0))

    screen.blit(title, title.get_rect(center=(screen.get_width()//2, 120)))
    screen.blit(hint1, hint1.get_rect(center=(screen.get_width()//2, 360)))
    screen.blit(hint2, hint2.get_rect(center=(screen.get_width()//2, 410)))

    if level_files:
        lvl_text = PIXELTYPE_SMALL.render(f"Level: {level_files[selected_level_idx]}", True, (0, 0, 0))
    else:
        lvl_text = PIXELTYPE_SMALL.render("No levels found in /levels", True, (200, 0, 0))
    screen.blit(lvl_text, lvl_text.get_rect(center=(screen.get_width() // 2, 480)))

#CLASSES

# deze class maakt de blokken aan deze kunnen worden geupdate en getekend op het scherm
class Tile(pygame.sprite.Sprite):
    def __init__(self, gx, gy, tile_id):
        super().__init__()
        self.image = tile_surfaces[tile_id]
        self.rect = self.image.get_rect(topleft=(gx * grid_size, gy * grid_size))

    def draw(self):
        screen.blit(self.image, cam.apply_rect(self.rect))


# dit is de class om de stopwatch te maken, deze kan worden gestart, gereset en de tijd kan worden opgevraagd in seconden of in een string in het formaat mm:ss.ms
class Stopwatch:
    def __init__(self):
        self.start_time = None
    
    def start(self):
        if self.start_time is None:
            self.start_time = time.time()
    
    def get_time(self):
        if self.start_time is None:
            return 0
        return time.time() - self.start_time
    
    def reset(self):
        self.start_time = time.time()
    
    def get_formatted_time(self):
        elapsed = self.get_time()
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        milliseconds = int((elapsed % 1) * 100)

# deze class maakt de knoppen aan, deze kunnen worden geupdate en getekend op het scherm.
# De knoppen kunnen ook transparant zijn, en er kan tekst op worden gezet met een bepaalde fontgrootte en offset.
class Button(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,Transparent, color,fontsize, fontoffsetX, fontoffsetY, text):
        super().__init__()
        self.image = pygame.Surface((w,h))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.topleft = [x , y]
        self.font = pygame.font.SysFont('Arial', fontsize)
        self.fontoffsetX = fontoffsetX
        self.fontoffsetY = fontoffsetY
        self.Transparent = Transparent
        self.text = text
    def update(self):
        pass
    def draw(self):
        if not self.Transparent:
            screen.blit(self.image, [self.rect.topleft,self.rect.topleft])
        text_surface = self.font.render(self.text, True, BLACK)
        screen.blit(text_surface, [self.rect.topleft[0] + self.fontoffsetX, self.rect.topleft[1]])

class Projectile(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
    def start(self, x, y, w ,h, angle, speed):
        self.active = True
        self.image = pygame.Surface((w, h))
        self.transformed_image = pygame.transform.rotate(self.image, -math.degrees(angle))
        self.rect = self.transformed_image.get_rect()
        self.transformed_image.fill(RED)
        self.rect.centerx = x
        self.rect.centery = y
        self.angle = angle
        self.speed = speed
    def update(self):
        self.alphax = math.cos(self.angle) * self.speed
        self.alphay = math.sin(self.angle) * self.speed
        self.rect.centerx += self.alphax
        self.rect.centery += self.alphay
    def draw(self, screen, cam):
        screen.blit(self.transformed_image, cam.apply_rect(self.rect))


#VARIABLES 2


# hier zijn de player, gun, blocks, buttons en stopwatch aangemaakt, en de camera is ingesteld om te volgen op de player
cam = Camera(SCREENSIZE)

player_group.add(Player(500,0,50,50,BLUE))
player = player_group.sprite

gun_group.add(Gun(10,10))
gun = gun_group.sprite

button1 = Button(500, 50, 175, 30, True, GREEN,
                 30, 5,fontoffsetY= -3,text= 'BULLETS:  ' + str(gun.bullets))
button2 = Button(500,100, 175, 30, True, GREEN,
                 30, 5,fontoffsetY= -3,text= 'BULLET TYPE: ' + str(gun.bullet_type))

stopwatch = Stopwatch()
stopwatch.start()

button3 = Button(500,150, 175, 30, True, GREEN,
                 30, 5,fontoffsetY= -3,text= 'TIME: 00:00.00')
hook = Hook()

# for y,i in enumerate(level):
#    for x,j in enumerate(i):
 #       if j == "X":
 #           blocks.add(Blocks(x*64,y*64,64,64,GREEN))
        # if j == "P":
        #     player.add(Player(x*64,y*64,50,50,BLUE))

#WHILE LOOP

# dit is de grote game loop, hier worden alle events afgehandeld, het scherm wordt geupdate en getekend.
while True:
    # -------------------- EVENTS --------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.VIDEORESIZE:
            SCREENSIZE = [event.w, event.h]
            cam.resize(SCREENSIZE)
            screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.RESIZABLE, vsync=1)

        # menu input
        if state == "menu":
            if state == "menu":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP and level_files:
                        selected_level_idx = (selected_level_idx - 1) % len(level_files)
                        selected_level_path = os.path.join(LEVEL_DIR, level_files[selected_level_idx])

                    elif event.key == pygame.K_DOWN and level_files:
                        selected_level_idx = (selected_level_idx + 1) % len(level_files)
                        selected_level_path = os.path.join(LEVEL_DIR, level_files[selected_level_idx])

                    elif event.key == pygame.K_RETURN:
                        player.reset_position()
                        stopwatch.reset()

                        if selected_level_path:
                            matrix = load_level_matrix(selected_level_path)
                            build_blocks_from_matrix(matrix)

                        state = "game"


        # Game input
        elif state == "game":
            if event.type == pygame.MOUSEBUTTONDOWN:
                gun.shoot(player)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state = "menu"
                elif event.key == pygame.K_r:
                    if gun.bullet_type == 'SUPER':
                        gun.bullet_type = 'NORMAL'
                        gun.bullets = 2
                        print("NORMAL BULLET ACTIVATED")
                    else:
                        gun.bullet_type = 'SUPER'
                        gun.bullets = 2
                        print("SUPER BULLET ACTIVATED")
                elif event.key == pygame.K_t:
                    stopwatch.reset()
                    player.reset_position()
                elif event.key == pygame.K_h:
                    hook.hook(Projectile())

    #draw
    if state == "menu":
        draw_menu(screen)

    elif state == "game":
        screen.fill(WHITE)

        cam.update_center(player.rect)

        player.update(blocks, gun)
        gun.update(player, cam)
        hook.update(gun)

        for b in blocks:
            b.update()
            b.draw()

        button1.text = 'BULLETS: ' + str(gun.bullets)
        button2.text = 'BULLET TYPE: ' + str(gun.bullet_type)
        button3.text = 'TIME: ' + stopwatch.get_formatted_time()

        for b in buttons:
            b.update()
            b.draw()

        gun.draw(screen, cam)
        player.draw(screen, cam)
        hook.draw(screen, cam)

    pygame.display.flip()
    clock.tick(FPS)