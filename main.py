import pygame,sys
import json
import time
import math
from camera import Camera
from player import Player
from gun import Gun
from hook import HProjectile as hook
import os

pygame.font.init()
pygame.mixer.init()

font_klein = pygame.font.Font('Fonts/Pixeltype.ttf', 50)
font_menu = pygame.font.Font('Fonts/Pixeltype.ttf', 30)

fontArial = pygame.font.SysFont("Arial", 72)

volume = 100

fullscreen_text = font_klein.render("Fullscreen", True, (0,0,0))
fullscreen_rect = fullscreen_text.get_rect(center=(400,450))

hint3 = font_klein.render("Settings", True, (0, 0, 0))
settings_rect = hint3.get_rect(topright=(770, 50))

home = font_klein.render("Home", True, (0, 0, 0))
homekonp_rect = home.get_rect(topleft=(30,50))

plus_text = font_klein.render("+", True, (0, 0, 0))
plus_rect = plus_text.get_rect()

min_text = font_klein.render("-", True, (0, 0, 0))
min_rect = min_text.get_rect()

fullscreen = False

pygame.mixer.set_num_channels(40)
menu_intro = ("sounds/main_menu_intro.ogg")
menu_loop = "sounds/main_menu_loop.ogg"
ingame_intro = "sounds/ingame_intro.ogg"
ingame_loop = "sounds/ingame_loop.ogg"

#SFX
lvl_switch = pygame.mixer.Sound("sounds/Switch1.wav")
page_switch = pygame.mixer.Sound("sounds/Page_turn.wav")
page_not_found = pygame.mixer.Sound("sounds/error_sound2.mp3")

SCREENSIZE = [800,800]
EMPTY = 0
FPS = 60
pygame.font.get_fonts()
state = "menu"

level_files = [f"level{i}.json" for i in range(1, 21)]
level_id = 0
huidig_level = f"levels/{level_files[level_id]}"
end_rect = None
current_level_matrix = None
menu_page = 0
LEVELS_PER_PAGE = 10

level_times = {}

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
blocks = pygame.sprite.Group()
buttons = pygame.sprite.Group()

grid_size = 32
lowest = 0

with open("tiledata.json", "r") as f:
    tiledata = json.load(f)

tile_dicts = tiledata["tiles"]

tile_surfaces = []

for tile in tile_dicts:
    path = os.path.join("textures", tile["file"])
    surf = pygame.transform.scale(
        pygame.image.load(path).convert_alpha(),
        (grid_size, grid_size)
    )
    tile_surfaces.append(surf)
MUSIC_ENDEVENT = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(MUSIC_ENDEVENT)

current_music_state = None
current_loop = None
music_phase = None   # "intro" of "loop"


def start_music(state_name):
    global current_music_state, current_loop, music_phase

    if current_music_state == state_name:
        return

    current_music_state = state_name

    if state_name == "menu":
        intro = menu_intro
        loop = menu_loop
    elif state_name == "game":
        intro = ingame_intro
        loop = ingame_loop
    else:
        return

    current_loop = loop
    music_phase = "intro"

    pygame.mixer.music.stop()
    pygame.mixer.music.load(intro)
    pygame.mixer.music.play()
    pygame.mixer.music.queue(loop)


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
        offset = data.get("offset", [0, 0])
        return matrix, spawn, end_pos, offset
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return None, None, None, [0, 0]

def build_blocks_from_matrix(matrix, offset):
    global current_level_matrix

    current_level_matrix = matrix
    blocks.empty()
    if not matrix:
        return

    off_x, off_y = offset

    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if int(val) == EMPTY:
                continue

            tile_id = int(val) - 1
            if 0 <= tile_id < len(tile_surfaces):
                tile = Tile(x + off_x, y + off_y, tile_id)
                blocks.add(tile)
                info = tile_dicts[tile.tile_id]
                if info.get("spike", False):
                    tile.rect = tile.rect.inflate(-8, -4)
                if info.get("glide", False):
                    tile.friction = 0

def create_low_border():
    tiles = blocks.sprites()
    lowest = None
    for tile in tiles:
        if lowest is None or tile.rect.bottom > lowest:
            lowest = tile.rect.bottom
    return lowest

def reset_run_state():
    player.reset_position()
    gun.bullets = 2
    gun.bullet_type = 'NORMAL'
    gun.super_shots_left = 0
    stopwatch.reset()
    active_hook = None


def start_level(level_path):
    global end_rect

    matrix, spawn, end_pos, offset = load_level(level_path)
    off_x, off_y = offset

    build_blocks_from_matrix(matrix, offset)

    if spawn is not None:
        player.start_pos = (
            (spawn[0] + off_x) * grid_size + grid_size // 2,
            (spawn[1] + off_y) * grid_size + grid_size // 2,
        )

    if end_pos is not None:
        end_rect = pygame.Rect(
            (end_pos[0] + off_x) * grid_size,
            (end_pos[1] + off_y) * grid_size,
            grid_size,
            grid_size,
        )
    else:
        end_rect = None

    reset_run_state()


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

def tile_function_update():
    for tile in blocks:
        info = tile_dicts[tile.tile_id]
        if info.get("super_pickup", False):
            if player.rect.colliderect(tile.rect):
                tile.kill()
                gun.activate_super_shots(2)
        elif info.get("spike", False):
            if player.rect.colliderect(tile.rect):
                start_level(huidig_level)
                lowest = create_low_border()
                reset_run_state()


def draw_menu(screen):
    """
    Draws a level selection menu with numbered buttons.
    Shows 10 levels per page.
    """

    screen.fill((125, 190, 255))

    title = font_klein.render("Rage Game", True, (0, 0, 0))
    screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 80))

    page_text = font_menu.render(f"Page {menu_page + 1}", True, BLACK)
    screen.blit(page_text, (screen.get_width() // 2 - page_text.get_width() // 2, 140))

    start_y = 200
    button_w = 160
    button_h = 40

    start_index = menu_page * LEVELS_PER_PAGE
    end_index = min(start_index + LEVELS_PER_PAGE, len(level_files))

    for button_index, level_index in enumerate(range(start_index, end_index)):
        x = screen.get_width() // 2 - button_w // 2
        y = start_y + button_index * 50

        rect = pygame.Rect(x, y, button_w, button_h)

        if level_index == level_id:
            pygame.draw.rect(screen, GREEN, rect)
        else:
            pygame.draw.rect(screen, WHITE, rect)

        pygame.draw.rect(screen, BLACK, rect, 2)

        try:
            text = font_menu.render(f"{str(level_index + 1)} {level_times[level_index]}" , True, BLACK)
        except:
            text = font_menu.render(str(level_index + 1), True, BLACK)


        screen.blit(text, text.get_rect(center=rect.center))

    hint = font_menu.render("LEFT/RIGHT = page   UP/DOWN = level   ENTER = play", True, BLACK)
    screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, 740)))
    screen.blit(hint3, settings_rect)

def draw_settings(screen):

    screen.fill((125, 190, 225))

    # tekst
    volume_text = font_klein.render("Volume" + str(volume), True, (0, 0, 0))
    volume_rect = volume_text.get_rect(center=(400, 300))

    # plus links
    plus_rect.midright = (volume_rect.left - 10, volume_rect.centery)

    # min rechts
    min_rect.midleft = (volume_rect.right + 10, volume_rect.centery)

    screen.blit(home, homekonp_rect)
    screen.blit(volume_text, volume_rect)
    screen.blit(plus_text, plus_rect)
    screen.blit(min_text, min_rect)
    screen.blit(fullscreen_text, fullscreen_rect)


def toggle_fullscreen():
    global screen, fullscreen

    fullscreen = not fullscreen

    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode(SCREENSIZE, pygame.RESIZABLE, vsync=1)

#CLASSES

# deze class maakt de tiles aan deze kunnen worden geupdate en getekend op het scherm
class Tile(pygame.sprite.Sprite):
    def __init__(self, gx, gy, tile_id):
        super().__init__()
        self.tile_id = tile_id
        self.image = tile_surfaces[self.tile_id]
        self.info = tile_dicts[tile_id]
        self.friction = 30
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

buttons.add(button1,button2,button3)
start_music("menu")
active_hook = None

# dit is de grote game loop, hier worden alle events afgehandeld, het scherm wordt geupdate en getekend.
while True:
    # -------------------- EVENTS --------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == MUSIC_ENDEVENT:
            if music_phase == "intro":
                music_phase = "loop"
            else:
                pygame.mixer.music.load(current_loop)
                pygame.mixer.music.play(-1)

        if event.type == pygame.VIDEORESIZE:
            SCREENSIZE = [event.w, event.h]
            cam.resize(SCREENSIZE)
            screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.RESIZABLE, vsync=1)

        # menu input
        if state == "menu":

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if settings_rect.collidepoint(event.pos):
                    state = "settings"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                button_w = 80
                button_h = 40
                start_y = 200

                start_index = menu_page * LEVELS_PER_PAGE
                end_index = min(start_index + LEVELS_PER_PAGE, len(level_files))

                for button_index, level_index in enumerate(range(start_index, end_index)):
                    x = screen.get_width() // 2 - button_w // 2
                    y = start_y + button_index * 50
                    rect = pygame.Rect(x, y, button_w, button_h)

                    if rect.collidepoint(event.pos):
                        level_id = level_index
                        huidig_level = f"levels/{level_files[level_id]}"
                        lvl_switch.play()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if level_id > 0:
                        level_id -= 1
                        huidig_level = f"levels/{level_files[level_id]}"
                        lvl_switch.play()

                        # automatically switch page if needed
                        menu_page = level_id // LEVELS_PER_PAGE
                elif event.key == pygame.K_DOWN:
                     if level_id < len(level_files) - 1:
                        level_id += 1
                        huidig_level = f"levels/{level_files[level_id]}"
                        lvl_switch.play()

                        # automatically switch page if needed
                        menu_page = level_id // LEVELS_PER_PAGE

                elif event.key == pygame.K_RIGHT:
                    max_page = (len(level_files) - 1) // LEVELS_PER_PAGE
                    if menu_page < max_page:
                        menu_page += 1
                        level_id = menu_page * LEVELS_PER_PAGE
                        huidig_level = f"levels/{level_files[level_id]}"
                        page_switch.play()
                    else:
                        page_not_found.play()

                elif event.key == pygame.K_LEFT:
                    if menu_page > 0:
                        menu_page -= 1
                        level_id = menu_page * LEVELS_PER_PAGE
                        huidig_level = f"levels/{level_files[level_id]}"
                        page_switch.play()
                    else:
                        page_not_found.play()



                elif event.key == pygame.K_RETURN:
                    if huidig_level:
                        start_level(huidig_level)
                        lowest = create_low_border()
                        start_music("game")
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
                    start_music('menu')
                elif event.key == pygame.K_r:
                    if gun.bullet_type == 'SUPER':
                        gun.bullet_type = 'NORMAL'
                        gun.super_shots_left = 0
                        #print("NORMAL BULLET ACTIVATED")
                    else:
                        gun.activate_super_shots(2)
                        #print("SUPER BULLET ACTIVATED")
                elif event.key == pygame.K_t:
                    start_level(huidig_level)
                    lowest = create_low_border()
                    reset_run_state()
                elif event.key == pygame.K_h:
                    if not active_hook:
                        active_hook = hook(player.rect.centerx, player.rect.centery, 10,10, gun.angle,30)
                    else:
                        player.derope()
                        active_hook = None

        elif state == "settings":
            draw_settings(screen)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if homeknp_rect.collidepoint(event.pos):
                    state = "menu"

                if fullscreen_rect.collidepoint(event.pos):
                    toggle_fullscreen()

                if plus_rect.collidepoint(event.pos):
                    if volume < 100:
                        volume += 1
                        pygame.mixer.music.set_volume(volume / 100)

                if min_rect.collidepoint(event.pos):
                    if volume > 0:
                        volume -= 1
                        pygame.mixer.music.set_volume(volume / 100)

    # draw en update
    if state == "menu":
        draw_menu(screen)

    elif state == "game":
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(current_loop)
            pygame.mixer.music.play(-1)

        screen.fill(WHITE)

        screen.blit(speed_text, (20, 20))  # 20,20 = linksboven

        cam.update_center(player.rect)
        player.update(blocks, gun)
        if player.rect.bottom > lowest + 300:
            start_level(huidig_level)
            lowest = create_low_border()
            reset_run_state()
        tile_function_update()
        if end_rect and player.rect.colliderect(end_rect):
            state = "menu"
            # level_times[level_id] == stopwatch.get_formatted_time()
            # print(level_times[level_id])

            level_times.update({level_id:stopwatch.get_formatted_time()})
            print(level_times)
            start_music('menu')
        gun.update(player, cam)
        if active_hook:
            active_hook.update(blocks, player, cam, screen)
            active_hook.draw(screen, cam)

        vel_x = player.velx
        vel_y = player.vely

        speed = math.hypot(vel_x, vel_y)  # absolute snelheid
        speed_pixels = round(speed, 2)  # optioneel afronden

        speed_text = font_klein.render(f"Speed: {speed_pixels}", True, (0, 0, 0))
        screen.blit(speed_text, (20, 20))  # linksboven

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
        if end_rect:
            pygame.draw.rect(screen, (0, 120, 255), cam.apply_rect(end_rect), 3)

    elif state == "settings":
        if homekonp_rect.collidepoint(event.pos):
            state = "menu"
        if plus_rect.collidepoint(event.pos):

            if volume < 100:
                volume += 1
                pygame.mixer.music.set_volume(volume / 100)

        if min_rect.collidepoint(event.pos):

            if volume > 0:
                volume -= 1
                pygame.mixer.music.set_volume(volume / 100)

    pygame.display.flip()
    clock.tick(FPS)
