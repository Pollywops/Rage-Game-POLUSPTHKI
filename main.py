import pygame,sys
import json
import time
import math
from camera import Camera
from player import Player
from gun import Gun
from hook import Hook
import os

pygame.font.init()
pygame.mixer.init()

font_klein = pygame.font.Font('Fonts/Pixeltype.ttf', 50)

fontArial = pygame.font.SysFont("Arial", 72)


pygame.mixer.set_num_channels(40)
SCREENSIZE = [800,800]
EMPTY = 0
FPS = 60
pygame.font.get_fonts()
state = "menu"

level_files = sorted([f for f in os.listdir("levels") if f.lower().endswith(".json")])
level_id = 0
huidig_level = f"levels/{level_files[level_id]}"
end_rect = None

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
pickups = pygame.sprite.Group()

grid_size = 32

with open("tiledata.json", "r") as f:
    tiledata = json.load(f)

tile_dicts = tiledata["tiles"]
for i, t in enumerate(tile_dicts):
    print("TILE", i+1, t.get("name"), t.get("file"))

tile_surfaces = []

for tile in tile_dicts:
    path = os.path.join("textures", tile["file"])
    surf = pygame.transform.scale(
        pygame.image.load(path).convert_alpha(),
        (grid_size, grid_size)
    )
    tile_surfaces.append(surf)

# deze functie laadt alle level data uit json (level matrix + spawn)
def load_level_data(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


def set_player_spawn_from_level_data(level_data):
    if not level_data:
        return

    spawn_data = level_data.get("spawn")
    if isinstance(spawn_data, dict) and "x" in spawn_data and "y" in spawn_data:
        spawn_gx = int(spawn_data["x"])
        spawn_gy = int(spawn_data["y"])
    elif isinstance(spawn_data, list) and len(spawn_data) >= 2:
        spawn_gx = int(spawn_data[0])
        spawn_gy = int(spawn_data[1])
    else:
        return

    spawn_x = spawn_gx * grid_size + grid_size // 2
    spawn_y = spawn_gy * grid_size + grid_size // 2
    player.start_pos = (spawn_x, spawn_y)

def build_blocks_from_matrix(matrix):
    blocks.empty()
    if not matrix:
        return

    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if int(val) == EMPTY:
                continue

            tile_id = int(val) - 1
            if 0 <= tile_id < len(tile_surfaces):
                tile = Tile(x, y, tile_id)
                blocks.add(tile)

bouncing_lock = False

def tile_function_update(prev_vy):

    bouncing = False

    for tile in blocks:
        info = tile_dicts[tile.tile_id]

        if info.get("spike", False):
            if player.rect.colliderect(tile.rect):
                player.reset_position()
                gun.bullets = 2
                stopwatch.reset()

        if info.get("bouncy", False):
            feet = player.rect.move(0, 2)
            if feet.colliderect(tile.rect):
                bouncing = True

                if (not bouncing_lock) and old_vy > 0:
                    strength = info.get("strength", 1.5)
                    player.vely = -max(6, old_vy) * strength
                    bouncing_lock = True
    if not bouncing:
        bouncing_lock = False


def draw_menu(screen):
    screen.fill((255, 255, 255))

    title = font_klein.render("Rage Game", True, (0, 0, 0))
    hint1 = font_klein.render("ENTER = Play", True, (0, 0, 0))
    hint2 = font_klein.render("ESC = Quit", True, (0, 0, 0))

    screen.blit(title, title.get_rect(center=(screen.get_width()//2, 120)))
    screen.blit(hint1, hint1.get_rect(center=(screen.get_width()//2, 360)))
    screen.blit(hint2, hint2.get_rect(center=(screen.get_width()//2, 410)))

    if level_files:
        lvl_text = font_klein.render(f"Level: {level_files[level_id]}", True, (0, 0, 0))
    else:
        lvl_text = font_klein.render("No levels found in /levels", True, (200, 0, 0))
    screen.blit(lvl_text, lvl_text.get_rect(center=(screen.get_width() // 2, 480)))

#CLASSES

# deze class maakt de tiles aan deze kunnen worden geupdate en getekend op het scherm
class Tile(pygame.sprite.Sprite):
    def __init__(self, gx, gy, tile_id):
        super().__init__()
        self.tile_id = tile_id
        self.image = tile_surfaces[self.tile_id]
        self.rect = self.image.get_rect(topleft=(gx * grid_size, gy * grid_size))

    def draw(self):
        screen.blit(self.image, cam.apply_rect(self.rect))

#dit is de class voor de bullet pick ups
class Pickup(pygame.sprite.Sprite):
    def __init__(self, gx, gy, kind="super", image_path=None):
        super().__init__()
        self.kind = kind

        if image_path:
            self.image = pygame.transform.scale(
                pygame.image.load(image_path).convert_alpha(),
                (grid_size, grid_size),
            )
        else:
            self.image = pygame.Surface((grid_size, grid_size), pygame.SRCALPHA)
            self.image.fill((180, 60, 255))

        self.rect = self.image.get_rect(topleft=(gx * grid_size, gy * grid_size))

    def update(self):
        pass

    def draw(self):
        screen.blit(self.image, cam.apply_rect(self.rect))


def spawn_default_pickups():
    pickups.empty()
    pickups.add(Pickup(8, 8, "super"))
    pickups.add(Pickup(14, 6, "super"))


def collect_pickups():
    hits = pygame.sprite.spritecollide(player, pickups, True)
    for pickup in hits:
        if pickup.kind == "super":
            gun.activate_super_shots(2)


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
        return f"{minutes:02d}:{seconds:02d}.{milliseconds:02d}"

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

buttons.add(button1,button2,button3)

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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and level_files:
                    level_id = (level_id - 1) % len(level_files)
                    huidig_level = f"levels/{level_files[level_id]}"

                elif event.key == pygame.K_DOWN and level_files:
                    level_id = (level_id + 1) % len(level_files)
                    huidig_level = f"levels/{level_files[level_id]}"

                elif event.key == pygame.K_RETURN:
                    stopwatch.reset()

                    if huidig_level:
                        level_data = load_level_data(huidig_level)
                        matrix = level_data.get("level") if level_data else None
                        build_blocks_from_matrix(matrix)
                        print("Loaded tiles:", len(blocks))
                        set_player_spawn_from_level_data(level_data)
                        end_data = level_data.get("end") if level_data else None
                        if isinstance(end_data, list) and len(end_data) >= 2:
                            end_rect = pygame.Rect(int(end_data[0]) * grid_size, int(end_data[1]) * grid_size,
                                                   grid_size, grid_size)
                        else:
                            end_rect = None
                    player.reset_position()
                    spawn_default_pickups()
                    state = "game"
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()


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
                        gun.super_shots_left = 0
                        gun.bullets = 2
                        print("NORMAL BULLET ACTIVATED")
                    else:
                        gun.activate_super_shots(2)
                        print("SUPER BULLET ACTIVATED")
                elif event.key == pygame.K_t:
                    stopwatch.reset()
                    player.reset_position()
                    spawn_default_pickups()
                elif event.key == pygame.K_h:
                    hook.hook(Projectile())

    #draw en update
    if state == "menu":
        draw_menu(screen)

    elif state == "game":
        screen.fill(WHITE)

        cam.update_center(player.rect)

        old_vy = player.vely
        player.update(blocks, gun)
        tile_function_update(old_vy)
        if end_rect and player.rect.colliderect(end_rect ):
            state = "menu"
        collect_pickups()
        gun.update(player, cam)
        hook.update(gun)

        for b in blocks:
            b.update()
            b.draw()

        for p in pickups:
            p.update()
            p.draw()

        button1.text = 'BULLETS: ' + str(gun.bullets)
        button2.text = 'BULLET TYPE: ' + str(gun.bullet_type)
        button3.text = 'TIME: ' + stopwatch.get_formatted_time()

        for b in buttons:
            b.update()
            b.draw()

        gun.draw(screen, cam)
        player.draw(screen, cam)
        hook.draw(screen, cam)
        if end_rect:
            pygame.draw.rect(screen, (0, 120, 255), cam.apply_rect(end_rect), 3)

    pygame.display.flip()
    clock.tick(FPS)
