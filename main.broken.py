import pygame, sys
import json
import time
import math
from camera import Camera
from player import Player
from gun import Gun
from hook import HProjectile as hook
import os
import subprocess

SAVE_FILE = "save_data.json"

########## COLORS ##############
RED = (255, 0, 0)
GREEN = (0, 177, 64)
BLUE = (30, 144, 255)
ORANGE = (252, 76, 2)
YELLOW = (254, 221, 0)
PURPLE = (155, 38, 182)
AQUA = (0, 103, 127)
WHITE = (200, 200, 200)
BLACK = (30, 30, 30)
GRAY = (128, 128, 128)
##############################

def load_save():
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)  #Lees de opgeslagen data

        best_times = data.get("best_times", {})  #Pak best_times uit de data
        return {int(level): time for level, time in best_times.items()}  #Maak keys weer integers

    except (OSError, json.JSONDecodeError):
        return {}  #Geef een lege dictionary terug als laden mislukt


def save_best_times(best_times):
    data = {
        "best_times": {str(level): time for level, time in best_times.items()}
        #Maak de keys strings zodat JSON ze goed opslaat
    }

    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)  #Slaat de data op in het bestand

pygame.font.init()
pygame.mixer.init()

font_klein = pygame.font.Font("Fonts/Pixeltype.ttf", 70)
font_menu = pygame.font.Font("Fonts/Pixeltype.ttf", 30)
small_button_font = pygame.font.Font("Fonts/Pixeltype.ttf", 36)

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
show_speed = True
show_deaths = True
slider_dragging = False

pygame.mixer.set_num_channels(40)
menu_intro = "sounds/main_menu_intro.ogg"
menu_loop = "sounds/main_menu_loop.ogg"
ingame_intro = "sounds/ingame_intro.ogg"
ingame_loop = "sounds/ingame_loop.ogg"

lvl_switch = pygame.mixer.Sound("sounds/Switch1.wav")
page_switch = pygame.mixer.Sound("sounds/Page_turn.wav")
page_not_found = pygame.mixer.Sound("sounds/error_sound2.mp3")

SCREENSIZE = [800, 800]
EMPTY = 0
FPS = 60
state = "menu"

level_files = [f"level{i}.json" for i in range(1, 21)]
level_id = 0
huidig_level = f"levels/{level_files[level_id]}"
end_rect = None
current_level_matrix = None
menu_page = 0
LEVELS_PER_PAGE = 10

level_times = {}          #Bewaart tijden van levels tijdens het spelen
best_times = load_save()  #Laadt de beste opgeslagen tijden
deaths = 0                #Aantal deaths waar je mee start

complete_time = ""        #Tijd waarmee een level is gehaalt
complete_deaths = 0       #Aantal deaths wanneer je het level haalt

screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.RESIZABLE, vsync=1)
clock = pygame.time.Clock()
player_group = pygame.sprite.GroupSingle()
gun_group = pygame.sprite.GroupSingle()
blocks = pygame.sprite.Group()
buttons = pygame.sprite.Group()

grid_size = 32
lowest = 0

with open("tiledata.json", "r", encoding="utf-8") as file:
    tiledata = json.load(file)

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
music_phase = None

def get_settings_button_rect():
    text = small_button_font.render("Settings", True, BLACK)
    text_rect = text.get_rect(topright=(screen.get_width() - 20, 20))
    button_rect = pygame.Rect(text_rect.left - 10, text_rect.top - 6,
                              text_rect.width + 20, text_rect.height + 12)
    return text, text_rect, button_rect

def get_editor_button_rect():
    text = small_button_font.render("Editor", True, BLACK)
    text_rect = text.get_rect(topleft=(20, 20))
    button_rect = pygame.Rect(text_rect.left - 10, text_rect.top - 6,
                              text_rect.width + 20, text_rect.height + 12)
    return text, text_rect, button_rect

def get_home_button_rect():
    text = small_button_font.render("Menu", True, BLACK)
    text_rect = text.get_rect(topleft=(20, 20))
    button_rect = pygame.Rect(text_rect.left - 10, text_rect.top - 6,
                              text_rect.width + 20, text_rect.height + 12)
    return text, text_rect, button_rect

def draw_small_button(screen, text, text_rect, button_rect):
    pygame.draw.rect(screen, WHITE, button_rect)
    pygame.draw.rect(screen, BLACK, button_rect, 2)
    screen.blit(text, text_rect)

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

def krijg_info(data, key):
    marker = data.get(key)
    if marker is None:
        return None
    return int(marker[0]), int(marker[1])

def start_level_editor():
    pygame.quit()
    subprocess.Popen([sys.executable, "lvleditor.py"])
    sys.exit()

def load_level(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    matrix = data.get("level")
    spawn = krijg_info(data, "spawn")
    end_pos = krijg_info(data, "end")
    offset = data.get("offset", [0, 0])

    return matrix, spawn, end_pos, offset

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

def reset_run_state(die):
    global deaths, huidig_level
    gun.bullets = 2
    gun.bullet_type = "NORMAL"
    gun.super_shots_left = 0
    stopwatch.reset()
    start_level(huidig_level)

    player.reset_position()
    player.derope()      # stop rope physics
    active_hook = None   # delete the hook projectile

    if die:
        deaths += 1          #Tel een death erbij op
        cam.add_shake()      #Laat de camera schudden
    active_hook = None       #Verwijder een actieve hook

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
                reset_run_state(True)

def draw_menu(screen):

    screen.fill((125, 190, 255))

    title = font_klein.render("Speed Shot", True, BLACK)
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

        pygame.draw.rect(screen, GREEN if level_index == level_id else WHITE, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)

        if level_index in best_times:
            text = font_menu.render(f"{level_index + 1}  {best_times[level_index]}", True, BLACK)
        else:
            text = font_menu.render(str(level_index + 1), True, BLACK)

        screen.blit(text, text.get_rect(center=rect.center))

    hint = font_menu.render("LEFT/RIGHT = page   UP/DOWN = level   ENTER = play", True, BLACK)
    screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, 740)))

    # settings + editor knoppen
    s_text, s_text_rect, s_button_rect = get_settings_button_rect()
    draw_small_button(screen, s_text, s_text_rect, s_button_rect)

    e_text, e_text_rect, e_button_rect = get_editor_button_rect()
    draw_small_button(screen, e_text, e_text_rect, e_button_rect)

def toggle_fullscreen():
    global screen, fullscreen

    fullscreen = not fullscreen

    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode(SCREENSIZE, pygame.RESIZABLE, vsync=1)

def time_to_seconds(s):
    try:
        m, rest = s.split(":")         #Splitst minuten van de rest
        sec, ms = rest.split(".")      #Splitst seconden en milliseconden
        return int(m) * 60 + int(sec) + int(ms) / 100
        #Zet alles om naar totale tijd in seconden
    except Exception:"inf")
        return float("inf")            #Als het fout gaat dan geef infinity terug
def _parse_time(s):
    return time_to_seconds(s)
def draw_level_complete(screen):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))       #Maakt een zwarte transparante achtergrond
    screen.blit(overlay, (0, 0))       #Maakt een zwarte transparante achtergrond
    screen.blit(overlay, (0, 0))
    cx = screen.get_width() // 2       #Middelpunt van het scherm
    cx = screen.get_width() // 2       #Middelpunt van het scherm
    title = font_klein.render("Level Complete!", True, (255, 220, 50))
    screen.blit(title, title.get_rect(center=(cx, 200)))  #Titel bovenaan
    screen.blit(title, title.get_rect(center=(cx, 200)))  #Titel bovenaan
    time_surf = font_klein.render(f"Time:   {complete_time}", True, (255, 255, 255))
    screen.blit(time_surf, time_surf.get_rect(center=(cx, 290)))  #Laat je tijd zien
    screen.blit(time_surf, time_surf.get_rect(center=(cx, 290)))  #Laat je tijd zien
    death_surf = font_klein.render(f"Deaths: {complete_deaths}", True, (255, 100, 100))
    screen.blit(death_surf, death_surf.get_rect(center=(cx, 360)))  #Laat aantal deaths zien
    screen.blit(death_surf, death_surf.get_rect(center=(cx, 360)))  #Laat aantal deaths zien
    best = best_times.get(level_id, None)   #Haalt de beste tijd van dit level op
    if best:est_times.get(level_id, None)   #Haalt de beste tijd van dit level op
        best_surf = font_menu.render(f"Best: {best}", True, (100, 255, 180))
        screen.blit(best_surf, best_surf.get_rect(center=(cx, 430)))  #Laat beste tijd zien
        screen.blit(best_surf, best_surf.get_rect(center=(cx, 430)))  #Laat beste tijd zien
    hint = font_menu.render("Press ENTER to continue", True, (180, 180, 180))
    screen.blit(hint, hint.get_rect(center=(cx, 520))) True, (180, 180, 180))
    screen.blit(hint, hint.get_rect(center=(cx, 520)))
bg_raw = pygame.image.load("textures/background.png").convert()
bg_raw = pygame.image.load("textures/background.png").convert()
def make_background(screen_size):
    sw, sh = screen_sizeen_size):
    sw, sh = screen_size
    scale = 1.35
    bw = int(sw * scale)
    bh = int(sh * scale)
    bh = int(sh * scale)
    return pygame.transform.smoothscale(bg_raw, (bw, bh))
    return pygame.transform.smoothscale(bg_raw, (bw, bh))
def draw_background(screen, background, player):
    sw, sh = SCREENSIZEeen, background, player):
    bw, bh = background.get_size()
    bw, bh = background.get_size()
    parallax_x = 0.05
    parallax_y = 0.02
    parallax_y = 0.02
    dx = player.rect.centerx - player.start_pos[0]
    dy = player.rect.centery - player.start_pos[1]
    dy = player.rect.centery - player.start_pos[1]
    base_x = (sw - bw) / 2
    base_y = (sh - bh) / 2
    base_y = (sh - bh) / 2
    bg_x = base_x - dx * parallax_x
    bg_y = base_y - dy * parallax_y
    bg_y = base_y - dy * parallax_y
    bg_x = max(sw - bw, min(0, bg_x))
    bg_y = max(sh - bh, min(0, bg_y))
    bg_y = max(sh - bh, min(0, bg_y))
    screen.blit(background, (bg_x, bg_y))
    screen.blit(background, (bg_x, bg_y))
background = make_background(SCREENSIZE)
background = make_background(SCREENSIZE)
class Tile(pygame.sprite.Sprite):
    def __init__(self, gx, gy, tile_id):
        super().__init__() gy, tile_id):
        self.tile_id = tile_id
        self.image = tile_surfaces[self.tile_id]
        self.info = tile_dicts[tile_id].tile_id]
        self.friction = 30icts[tile_id]
        self.rect = self.image.get_rect(topleft=(gx * grid_size, gy * grid_size))
        self.rect = self.image.get_rect(topleft=(gx * grid_size, gy * grid_size))
    def update(self):
        passte(self):
        pass
    def draw(self):
        screen.blit(self.image, cam.apply_rect(self.rect))
        screen.blit(self.image, cam.apply_rect(self.rect))
class Stopwatch:
    def __init__(self):
        self.start_time = None
        self.start_time = None
    def start(self):
        if self.start_time is None:
            self.start_time = time.time()
            self.start_time = time.time()
    def get_time(self):
        if self.start_time is None:
            return 0t_time is None:
        return time.time() - self.start_time
        return time.time() - self.start_time
    def reset(self):
        self.start_time = None
        self.start_time = None
    def get_formatted_time(self):
        elapsed = self.get_time()
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60))
        milliseconds = int((elapsed % 1) * 100)
        return f"{minutes:02d}:{seconds:02d}.{milliseconds:02d}"
        return f"{minutes:02d}:{seconds:02d}.{milliseconds:02d}"
class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, transparent, color, fontsize, fontoffsetX, fontoffsetY, text):
        super().__init__()y, w, h, transparent, color, fontsize, fontoffsetX, fontoffsetY, text):
        self.image = pygame.Surface((w, h))
        self.image.fill(color)rface((w, h))
        self.rect = self.image.get_rect()
        self.rect.topleft = [x, y]_rect()
        self.font = pygame.font.SysFont("Arial", fontsize)
        self.fontoffsetX = fontoffsetXt("Arial", fontsize)
        self.fontoffsetY = fontoffsetY
        self.transparent = transparent
        self.text = text = transparent
        self.text = text
    def update(self):
        passte(self):
        pass
    def draw(self):
        if not self.transparent:
            screen.blit(self.image, [self.rect.topleft, self.rect.topleft])
        text_surface = self.font.render(self.text, True, BLACK)ct.topleft])
        screen.blit(text_surface, [self.rect.topleft[0] + self.fontoffsetX, self.rect.topleft[1]])
        screen.blit(text_surface, [self.rect.topleft[0] + self.fontoffsetX, self.rect.topleft[1]])
cam = Camera(SCREENSIZE)
cam = Camera(SCREENSIZE)
player_group.add(Player(500, 0, 50, 50, BLUE))
player = player_group.sprite 0, 50, 50, BLUE))
player = player_group.sprite
gun_group.add(Gun(10, 10))
gun = gun_group.sprite10))
gun = gun_group.sprite
button1 = Button(500, 50, 175, 30, True, GREEN, 30, 5, -3, "BULLETS:  " + str(gun.bullets))
button2 = Button(500, 100, 175, 30, True, GREEN, 30, 5, -3, "BULLET TYPE: " + str(gun.bullet_type))
button3 = Button(500, 150, 175, 30, True, GREEN, 30, 5, -3, "TIME: 00:00.00") str(gun.bullet_type))
button3 = Button(500, 150, 175, 30, True, GREEN, 30, 5, -3, "TIME: 00:00.00")
buttons.add(button1, button2, button3)
buttons.add(button1, button2, button3)
stopwatch = Stopwatch()
stopwatch.start()atch()
stopwatch.start()
start_music("menu")
active_hook = None)
active_hook = None
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()pygame.QUIT:
            sys.exit()t()
            sys.exit()
        if event.type == MUSIC_ENDEVENT:
            if music_phase == "intro":T:
                music_phase = "loop"":
            else:usic_phase = "loop"
                pygame.mixer.music.load(current_loop)
                pygame.mixer.music.play(-1)rent_loop)
                pygame.mixer.music.play(-1)
        if event.type == pygame.VIDEORESIZE:
            SCREENSIZE = [event.w, event.h]:
            background = make_background(SCREENSIZE)
            cam.resize(SCREENSIZE)ground(SCREENSIZE)
            screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.RESIZABLE, vsync=1)
            screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.RESIZABLE, vsync=1)
        # menu input
        if state == "menu":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                _, _, settings_knop = get_settings_button_rect()ent.button == 1:
                _, _, editor_knop = get_editor_button_rect()

                if settings_knop.collidepoint(event.pos):.width + 12, settings_rect.height + 8)
                    state = "settings"depoint(event.pos):
                elif editor_knop.collidepoint(event.pos):
                    start_level_editor()point(event.pos):
                else:tart_level_editor()
                    button_w = 160
                    button_h = 400
                    start_y = 200
                    start_y = 200
                    start_index = menu_page * LEVELS_PER_PAGE
                    end_index = min(start_index + LEVELS_PER_PAGE, len(level_files))
                    end_index = min(start_index + LEVELS_PER_PAGE, len(level_files))
                    for button_index, level_index in enumerate(range(start_index, end_index)):
                        x = screen.get_width() // 2 - button_w // 2e(start_index, end_index)):
                        y = start_y + button_index * 50utton_w // 2
                        rect = pygame.Rect(x, y, button_w, button_h)
                        rect = pygame.Rect(x, y, button_w, button_h)
                        if rect.collidepoint(event.pos):
                            level_id = level_index.pos):
                            huidig_level = f"levels/{level_files[level_id]}"
                            lvl_switch.play()levels/{level_files[level_id]}"
                            breakwitch.play()
                            break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if level_id > 0:me.K_UP:
                        level_id -= 1
                        huidig_level = f"levels/{level_files[level_id]}"
                        lvl_switch.play()levels/{level_files[level_id]}"
                        lvl_switch.play()
                        
                        menu_page = level_id // LEVELS_PER_PAGE
                        menu_page = level_id // LEVELS_PER_PAGE
                elif event.key == pygame.K_DOWN:
                    if level_id < len(level_files) - 1:
                        level_id += 1(level_files) - 1:
                        huidig_level = f"levels/{level_files[level_id]}"
                        lvl_switch.play()levels/{level_files[level_id]}"
                        lvl_switch.play()

                        menu_page = level_id // LEVELS_PER_PAGE
                        menu_page = level_id // LEVELS_PER_PAGE
                elif event.key == pygame.K_RIGHT:
                    max_page = (len(level_files) - 1) // LEVELS_PER_PAGE
                    if menu_page < max_page:les) - 1) // LEVELS_PER_PAGE
                        menu_page += 1_page:
                        level_id = menu_page * LEVELS_PER_PAGE
                        huidig_level = f"levels/{level_files[level_id]}"
                        page_switch.play()evels/{level_files[level_id]}"
                    else:age_switch.play()
                        page_not_found.play()
                        page_not_found.play()
                elif event.key == pygame.K_LEFT:
                    if menu_page > 0:ame.K_LEFT:
                        menu_page -= 1
                        level_id = menu_page * LEVELS_PER_PAGE
                        huidig_level = f"levels/{level_files[level_id]}"
                        page_switch.play()evels/{level_files[level_id]}"
                    else:age_switch.play()
                        page_not_found.play()
                        page_not_found.play()
                elif event.key == pygame.K_RETURN:
                    if huidig_level:game.K_RETURN:
                        deaths = 0l:
                        reset_run_state(False)
                        lowest = create_low_border()
                        start_music("game")_border()
                        state = "game"ame")
                        state = "game"
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit() pygame.K_ESCAPE:
                    sys.exit()t()
                    sys.exit()
        elif state == "game":
            if event.type == pygame.MOUSEBUTTONDOWN:
                gun.shoot(player)me.MOUSEBUTTONDOWN:
                stopwatch.start()
                stopwatch.start()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state = "menu"game.K_ESCAPE:
                    start_music("menu")
                elif event.key == pygame.K_t:
                    reset_run_state(False)_t:
                    lowest = create_low_border()
                elif event.key == pygame.K_h:r()
                    if not active_hook:e.K_h:
                        active_hook = hook(player.rect.centerx, player.rect.centery, 10, 10, gun.angle, 30)
                    else:ctive_hook = hook(player.rect.centerx, player.rect.centery, 10, 10, gun.angle, 30)
                        player.derope()
                        active_hook = None
                        active_hook = None

        elif state == "settings":
        elif state == "settings":
            cx = screen.get_width() // 2
            gap = 60een.get_width() // 2
            ty  = 385
            fs_rect  = pygame.Rect(cx + 10, ty,          TOGGLE_W, TOGGLE_H)
            spd_rect = pygame.Rect(cx + 10, ty + gap,    TOGGLE_W, TOGGLE_H)
            dth_rect = pygame.Rect(cx + 10, ty + gap * 2,TOGGLE_W, TOGGLE_H)
            slider   = get_slider_rect(screen) + gap * 2,TOGGLE_W, TOGGLE_H)
            home_knop = pygame.Rect(homekonp_rect.left - 6, homekonp_rect.top - 4,
                                    homekonp_rect.width + 12, homekonp_rect.height + 8)
                                    homekonp_rect.width + 12, homekonp_rect.height + 8)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if home_knop.collidepoint(event.pos):nd event.button == 1:
                    state = "menu"  # Terug naar menu
                    state = "menu"  # Terug naar menu
                elif fs_rect.collidepoint(event.pos):
                    toggle_fullscreen()  # Zet fullscreen aan of uit
                    background = make_background(SCREENSIZE)n of uit
                    background = make_background(SCREENSIZE)
                elif spd_rect.collidepoint(event.pos):
                    show_speed = not show_speed  #Speed Laten zien of niet
                    show_speed = not show_speed  #Speed Laten zien of niet
                elif dth_rect.collidepoint(event.pos):
                    show_deaths = not show_deaths  #Deaths Laten zien of niet
                    show_deaths = not show_deaths  #Deaths Laten zien of niet
                else:
                    slider_hitbox = pygame.Rect(slider.left, slider.top - 6, slider.width, slider.height + 12)
                    if slider_hitbox.collidepoint(event.pos):slider.top - 6, slider.width, slider.height + 12)
                        slider_dragging = Trueint(event.pos):
                        volume = int((event.pos[0] - slider.left) / slider.width * 100)
                        volume = max(0, min(100, volume))  #Houdt het volume tussen 0 en 100
                        pygame.mixer.music.set_volume(volume / 100)et volume tussen 0 en 100
                        pygame.mixer.music.set_volume(volume / 100)
            elif event.type == pygame.MOUSEBUTTONUP:
                slider_dragging = False  #Stop met verplaatsem van de slider
                slider_dragging = False  #Stop met verplaatsem van de slider
            elif event.type == pygame.MOUSEMOTION and slider_dragging:
                volume = int((event.pos[0] - slider.left) / slider.width * 100)
                volume = max(0, min(100, volume))  #Houd volume tussen 0 en 100
                pygame.mixer.music.set_volume(volume / 100)lume tussen 0 en 100
                pygame.mixer.music.set_volume(volume / 100)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                state = "menu"  #Als je op escape drukt dan ga je terug naar het menu
                state = "menu"  #Als je op escape drukt dan ga je terug naar het menu
    if state == "menu":
        draw_menu(screen)
        draw_menu(screen)
    elif state == "game":
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(current_loop)
            pygame.mixer.music.play(-1)rent_loop)
            pygame.mixer.music.play(-1)
        draw_background(screen, background, player)
        draw_background(screen, background, player)
        cam.update_center(player.rect)
        player.update(blocks, gun)ect)
        player.update(blocks, gun)
        if player.rect.bottom > lowest + 300:
            reset_run_state(True)owest + 300:
            reset_run_state(True)
        tile_function_update()
        tile_function_update()
        if end_rect and player.rect.colliderect(end_rect):
            complete_time = stopwatch.get_formatted_time()
            complete_deaths = deathsh.get_formatted_time()
            level_times[level_id] = complete_time
            if level_id not in best_times or stopwatch.get_time() < _parse_time(best_times[level_id]):
                best_times[level_id] = complete_timech.get_time() < _parse_time(best_times[level_id]):
                save_best_times(best_times)lete_time
                save_best_times(best_times)
            state = "level_complete"
            state = "level_complete"
        gun.update(player, cam)
        gun.update(player, cam)
        if active_hook:
            active_hook.update(blocks, player, cam, screen)
            active_hook.draw(screen, cam)ayer, cam, screen)
            active_hook.draw(screen, cam)
        vel_x = player.velx
        vel_y = player.vely
        vel_y = player.vely
        speed = math.hypot(vel_x, vel_y)
        if speed < 1:hypot(vel_x, vel_y)
            speed = 0
        speed_pixels = round(speed, 2)  # optioneel afronden
        speed_pixels = round(speed, 2)  # optioneel afronden
        if show_deaths:
            death_text = font_klein.render(f"Deaths: {deaths}", True, (200, 50, 50))
            screen.blit(death_text, (20, 20))Deaths: {deaths}", True, (200, 50, 50))
            screen.blit(death_text, (20, 20))
        if show_speed:
            speed_text = font_klein.render(f"Speed: {speed_pixels}", True, BLACK)
            screen.blit(speed_text, (20, screen.get_height() - 50)), True, BLACK)
            screen.blit(speed_text, (20, screen.get_height() - 50))
        for b in blocks:
            b.update()s:
            b.draw()()
            b.draw()
        button1.text = "BULLETS: " + str(gun.bullets)
        button2.text = "BULLET TYPE: " + str(gun.bullet_type)
        button3.text = "TIME: " + stopwatch.get_formatted_time()
        button3.text = "TIME: " + stopwatch.get_formatted_time()
        for b in buttons:
            b.update()ns:
            b.draw()()
            b.draw()
        if show_deaths:
            death_text = font_klein.render(f"Deaths: {deaths}", True, (200, 50, 50))
            screen.blit(death_text, (20, 20))Deaths: {deaths}", True, (200, 50, 50))
            screen.blit(death_text, (20, 20))
        if show_speed:
            speed_text = font_klein.render(f"Speed: {speed_pixels}", True, BLACK)
            screen.blit(speed_text, (20, screen.get_height() - 50)), True, BLACK)
            screen.blit(speed_text, (20, screen.get_height() - 50))
        gun.draw(screen, cam)
        player.draw(screen, cam)
        player.draw(screen, cam)
        if end_rect:
            pygame.draw.rect(screen, (0, 120, 255), cam.apply_rect(end_rect), 3)
            pygame.draw.rect(screen, (0, 120, 255), cam.apply_rect(end_rect), 3)
    elif state == "settings":
        draw_settings(screen)
        draw_settings(screen)
    elif state == "level_complete":
        draw_level_complete(screen)
        draw_level_complete(screen)
    cam.update_shake()
    pygame.display.flip()
    clock.tick(FPS)flip()
    clock.tick(FPS)