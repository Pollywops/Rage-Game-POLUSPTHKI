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
font_menu = pygame.font.Font('Fonts/Pixeltype.ttf', 30)

fontArial = pygame.font.SysFont("Arial", 72)


pygame.mixer.set_num_channels(40)
SCREENSIZE = [800,800]
EMPTY = 0
FPS = 60
pygame.font.get_fonts()
state = "menu"

level_files = [f"level{i}.json" for i in range(1, 11)]
level_id = 0
huidig_level = f"levels/{level_files[level_id]}"
end_rect = None
current_level_matrix = None

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

def parse_marker(data, key):
    marker = data.get(key)
    if isinstance(marker, dict) and "x" in marker and "y" in marker:
        return int(marker["x"]), int(marker["y"])
    if isinstance(marker, list) and len(marker) >= 2:
        return int(marker[0]), int(marker[1])
    return None


def load_level(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        matrix = data.get("level")
        spawn = parse_marker(data, "spawn")
        end_pos = parse_marker(data, "end")
        return matrix, spawn, end_pos
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return None, None, None

def build_blocks_from_matrix(matrix):
    global current_level_matrix

    current_level_matrix = matrix
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


def reset_run_state():
    player.reset_position()
    gun.bullets = 2
    gun.bullet_type = 'NORMAL'
    gun.super_shots_left = 0
    hook.hooking = False
    stopwatch.reset()
    spawn_default_pickups()


def start_level(level_path):
    global end_rect

    matrix, spawn, end_pos = load_level(level_path)
    build_blocks_from_matrix(matrix)

    if spawn is not None:
        player.start_pos = (
            spawn[0] * grid_size + grid_size // 2,
            spawn[1] * grid_size + grid_size // 2,
        )

    if end_pos is not None:
        end_rect = pygame.Rect(
            end_pos[0] * grid_size,
            end_pos[1] * grid_size,
            grid_size,
            grid_size,
        )
    else:
        end_rect = None

    reset_run_state()


def is_kill_tile(tile_info):
    return bool(
        tile_info.get("kill", False)
        or tile_info.get("spike", False)
        or tile_info.get("hazard", False)
    )


def get_tile_info_at_world(x, y):
    if not current_level_matrix:
        return None

    gx = int(x // grid_size)
    gy = int(y // grid_size)

    if gy < 0 or gy >= len(current_level_matrix):
        return None

    row = current_level_matrix[gy]
    if gx < 0 or gx >= len(row):
        return None

    try:
        raw = int(row[gx])
    except (TypeError, ValueError):
        return None

    if raw == EMPTY:
        return None

    tile_id = raw - 1
    if tile_id < 0 or tile_id >= len(tile_dicts):
        return None

    return tile_dicts[tile_id]


def is_kill_at_world(x, y):
    tile_info = get_tile_info_at_world(x, y)
    if tile_info is None:
        return False
    return is_kill_tile(tile_info)

bouncing_lock = False

def tile_function_update(prev_vy):
    global bouncing_lock

    check_points = [
        (player.rect.left + 1, player.rect.top + 1),
        (player.rect.right - 1, player.rect.top + 1),
        (player.rect.left + 1, player.rect.centery),
        (player.rect.right - 1, player.rect.centery),
        (player.rect.left + 2, player.rect.bottom - 1),
        (player.rect.centerx, player.rect.bottom - 1),
        (player.rect.right - 2, player.rect.bottom - 1),
        (player.rect.centerx, player.rect.centery),
    ]
    for px, py in check_points:
        if is_kill_at_world(px, py):
            reset_run_state()
            return

    bouncing = False
    feet = player.rect.move(0, 2)

    for tile in blocks:
        info = tile_dicts[tile.tile_id]

        if info.get("bouncy", False):
            if feet.colliderect(tile.rect):
                bouncing = True

                if (not bouncing_lock) and prev_vy > 0:
                    strength = info.get("strength", 1.5)
                    player.vely = -max(6, prev_vy) * strength
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

    lvl_text = font_menu.render(f"Selected: Level {level_id + 1}", True, (0, 0, 0))
    screen.blit(lvl_text, lvl_text.get_rect(center=(screen.get_width() // 2, 200)))

    button_w = 170
    button_h = 36
    col_gap = 80
    row_gap = 12
    cols = 2
    rows = 5
    total_w = cols * button_w + (cols - 1) * col_gap
    total_h = rows * button_h + (rows - 1) * row_gap
    start_x = screen.get_width() // 2 - total_w // 2
    start_y = screen.get_height() // 2 - total_h // 2 + 90

    for i in range(10):
        col = i % cols
        row = i // cols
        rect = pygame.Rect(
            start_x + col * (button_w + col_gap),
            start_y + row * (button_h + row_gap),
            button_w,
            button_h,
        )
        color = GREEN if i == level_id else BLACK
        txt = font_menu.render(f"Level {i + 1}", True, color)
        screen.blit(txt, txt.get_rect(center=rect.center))

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
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                button_w = 170
                button_h = 36
                col_gap = 80
                row_gap = 12
                cols = 2
                rows = 5
                total_w = cols * button_w + (cols - 1) * col_gap
                total_h = rows * button_h + (rows - 1) * row_gap
                start_x = screen.get_width() // 2 - total_w // 2
                start_y = screen.get_height() // 2 - total_h // 2 + 90

                for i in range(10):
                    col = i % cols
                    row = i // cols
                    rect = pygame.Rect(
                        start_x + col * (button_w + col_gap),
                        start_y + row * (button_h + row_gap),
                        button_w,
                        button_h,
                    )
                    if rect.collidepoint(event.pos):
                        level_id = i
                        huidig_level = f"levels/{level_files[level_id]}"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    level_id = (level_id - 1) % len(level_files)
                    huidig_level = f"levels/{level_files[level_id]}"

                elif event.key == pygame.K_DOWN:
                    level_id = (level_id + 1) % len(level_files)
                    huidig_level = f"levels/{level_files[level_id]}"

                elif event.key == pygame.K_RETURN:
                    if huidig_level:
                        start_level(huidig_level)
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
                    reset_run_state()
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
