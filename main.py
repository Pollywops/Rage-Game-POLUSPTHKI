import pygame,sys
import json
import time
import math
from camera import Camera
from player import Player
from gun import Gun
from hook import HProjectile as hook
import os

SAVE_FILE = "save_data.json"

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

font_klein = pygame.font.Font('Fonts/Pixeltype.ttf', 50)
font_menu = pygame.font.Font('Fonts/Pixeltype.ttf', 30)

fontArial = pygame.font.SysFont("Arial", 72)

volume = 100  #Start volume

fullscreen_text = font_klein.render("Fullscreen", True, (0, 0, 0))
fullscreen_rect = fullscreen_text.get_rect(center=(400, 450))  #Positie van de fullscreen knop

hint3 = font_klein.render("Settings", True, (0, 0, 0))
settings_rect = hint3.get_rect(topright=(770, 50))  #Positie van de settings knop

home = font_klein.render("Home", True, (0, 0, 0))
homeknop_rect = home.get_rect(topleft=(30, 50))  #Positie van de home knop

#Start settings
fullscreen = False
show_speed = True
show_deaths = True
slider_dragging = False

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

level_times = {}          #Bewaart tijden van levels tijdens het spelen
best_times = load_save()  #Laadt de beste opgeslagen tijden
deaths = 0                #Aantal deaths waar je mee start

complete_time = ""        #Tijd waarmee een level is gehaalt
complete_deaths = 0       #Aantal deaths wanneer je het level haalt

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

file = open("tiledata.json", "r")
tiledata = json.load(file)
file.close()

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
music_phase = None   #intro of loop


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


def krijg_info(data, type):
    marker = data.get(type)
    return int(marker[0]), int(marker[1])

def load_level(path):
    f = open(path, "r", encoding="utf-8")
    data = json.load(f)
    f.close()

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
deaths = 0

def reset_run_state(die):
    global deaths, huidig_level
    gun.bullets = 2
    gun.bullet_type = 'NORMAL'
    gun.super_shots_left = 0
    stopwatch.reset()
    start_level(huidig_level)
    player.reset_position()  #Zet de speler terug naar de startpositie
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
    #Kleur menu achtergrond
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

        if level_index in best_times:
            text = font_menu.render(f"{level_index + 1}  {best_times[level_index]}", True, BLACK)
            #Laat levelnummer en beste tijd zien
        else:
            text = font_menu.render(str(level_index + 1), True, BLACK)
            #Laat alleen het levelnummer zien


        screen.blit(text, text.get_rect(center=rect.center))

    hint = font_menu.render("LEFT/RIGHT = page   UP/DOWN = level   ENTER = play", True, BLACK)
    screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, 740)))

    #Settings knop rechts bovenaan
    settings_knop = pygame.Rect(settings_rect.left - 6, settings_rect.top - 4,
                                settings_rect.width + 12, settings_rect.height + 8)
    pygame.draw.rect(screen, WHITE, settings_knop)
    pygame.draw.rect(screen, BLACK, settings_knop, 2)
    screen.blit(hint3, settings_rect)

#Breedte en hoogte van de toggles en de volumebalk
TOGGLE_W = 300
TOGGLE_H = 46
KNOB_MARGE = 5       #Ruimte tussen de rand en het schuifblokje
SLIDER_W = 400
SLIDER_H = 30

def get_slider_rect(screen):
    cx = screen.get_width() // 2
    return pygame.Rect(cx - SLIDER_W // 2, 310, SLIDER_W, SLIDER_H)

#Tekent een knop
def knop(screen, rect, tekst, geselecteerd=False):
    kleur = GREEN if geselecteerd else WHITE
    pygame.draw.rect(screen, kleur, rect)
    pygame.draw.rect(screen, BLACK, rect, 2)
    lbl = font_menu.render(tekst, True, BLACK)
    screen.blit(lbl, lbl.get_rect(center=rect.center))

#Tekent een toggle met een schuifblokje, links=uit rechts=aan
def draw_sliding_toggle(screen, cx, y, label, value):
    lbl = font_menu.render(label, True, BLACK)
    screen.blit(lbl, (cx - 260, y + (TOGGLE_H - lbl.get_height()) // 2))

    #Buitenste balk
    track = pygame.Rect(cx + 10, y, TOGGLE_W, TOGGLE_H)
    pygame.draw.rect(screen, WHITE, track)
    pygame.draw.rect(screen, BLACK, track, 2)

    #Vierkant blokje dat schuift
    knob_size = TOGGLE_H - KNOB_MARGE * 2
    knob_x = track.right - KNOB_MARGE - knob_size if value else track.left + KNOB_MARGE
    knob = pygame.Rect(knob_x, track.top + KNOB_MARGE, knob_size, knob_size)
    pygame.draw.rect(screen, (180, 180, 180), knob)
    pygame.draw.rect(screen, BLACK, knob, 2)

    #On en off tekst in de balk
    off_lbl = font_menu.render("OFF", True, BLACK)
    on_lbl  = font_menu.render("ON",  True, BLACK)
    midden_links  = track.left  + KNOB_MARGE + knob_size + (TOGGLE_W - knob_size - KNOB_MARGE * 2) // 4
    midden_rechts = track.right - KNOB_MARGE - knob_size - (TOGGLE_W - knob_size - KNOB_MARGE * 2) // 4
    screen.blit(off_lbl, off_lbl.get_rect(center=(midden_links,  track.centery)))
    screen.blit(on_lbl,  on_lbl.get_rect( center=(midden_rechts, track.centery)))

    return track

def draw_settings(screen):

    #Tekent achtergrond kleur
    screen.fill((125, 190, 255))
    cx = screen.get_width() // 2    #Midden van de X-as

    #Titel bovenaan het scherm
    title = font_klein.render("Settings", True, BLACK)
    screen.blit(title, title.get_rect(center=(cx, 70)))

    #Home knop
    home_knop = pygame.Rect(homeknop_rect.left - 6, homeknop_rect.top - 4,
                            homeknop_rect.width + 12, homeknop_rect.height + 8)
    knop(screen, home_knop, "Home")

    #Volume tekst boven de Volumebalk
    slider = get_slider_rect(screen)
    vol_lbl = font_menu.render(f"Volume: {volume}%", True, BLACK)
    screen.blit(vol_lbl, vol_lbl.get_rect(midbottom=(slider.centerx, slider.top - 4)))

    #Volumebalk achtergrond
    pygame.draw.rect(screen, WHITE, slider)
    pygame.draw.rect(screen, BLACK, slider, 2)

    #Gevulde deel van de balk
    fill_w = int(slider.width * volume / 100)
    fill = pygame.Rect(slider.left, slider.top, fill_w, slider.height)
    pygame.draw.rect(screen, (100, 160, 220), fill)

    #Schuifblokje in de volumebalk
    knob_x = max(slider.left, min(slider.left + fill_w - SLIDER_H // 2, slider.right - SLIDER_H))
    knob = pygame.Rect(knob_x, slider.top, SLIDER_H, SLIDER_H)
    pygame.draw.rect(screen, WHITE, knob)
    pygame.draw.rect(screen, BLACK, knob, 2)

    gap = 60 #Gat tussen de 2 opties
    ty = 385 #Y-as positie van de 2 opties

    #Opties
    #draw_sliding_toggle(screen, cx, ty,           "Fullscreen",   fullscreen)
    draw_sliding_toggle(screen, cx, ty + gap,     "Show Speed",   show_speed)
    draw_sliding_toggle(screen, cx, ty + gap * 2, "Show Deaths",  show_deaths)

    sep_y = ty + gap * 3 + 8

    ctrl_title = font_menu.render("Controls", True, BLACK)
    screen.blit(ctrl_title, ctrl_title.get_rect(center=(cx, sep_y + 16)))

    #Lijst met toetsen en wat ze doen
    controls = [
        ("Mouse click", "Shoot"),
        ("H",           "Hook"),
        ("R",           "Super bullet"),
        ("T",           "Reset"),
        ("ESC",         "Back to menu"),
    ]
    for i, (key, desc) in enumerate(controls):
        ry = sep_y + 44 + i * 26  #Berekend de Y-positie

        screen.blit(font_menu.render(key, True, BLACK), (cx - 180, ry))
        #Tekent de toets links

        screen.blit(font_menu.render(desc, True, BLACK), (cx + 20, ry))
        #Tekent de uitleg rechts

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
    except Exception:
        return float("inf")            #Als het fout gaat dan geef infinity terug


def draw_level_complete(screen):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))       #Maakt een zwarte transparante achtergrond
    screen.blit(overlay, (0, 0))

    cx = screen.get_width() // 2       #Middelpunt van het scherm

    title = font_klein.render("Level Complete!", True, (255, 220, 50))
    screen.blit(title, title.get_rect(center=(cx, 200)))  #Titel bovenaan

    time_surf = font_klein.render(f"Time:   {complete_time}", True, (255, 255, 255))
    screen.blit(time_surf, time_surf.get_rect(center=(cx, 290)))  #Laat je tijd zien

    death_surf = font_klein.render(f"Deaths: {complete_deaths}", True, (255, 100, 100))
    screen.blit(death_surf, death_surf.get_rect(center=(cx, 360)))  #Laat aantal deaths zien

    best = best_times.get(level_id, None)   #Haalt de beste tijd van dit level op
    if best:
        best_surf = font_menu.render(f"Best: {best}", True, (100, 255, 180))
        screen.blit(best_surf, best_surf.get_rect(center=(cx, 430)))  #Laat beste tijd zien

    hint = font_menu.render("Press ENTER to continue", True, (180, 180, 180))
    screen.blit(hint, hint.get_rect(center=(cx, 520)))
bg_raw = pygame.image.load('textures/background.png').convert()

def make_background(SCREENSIZE):
    sw, sh = SCREENSIZE

    scale = 1.35
    bw = int(sw * scale)
    bh = int(sh * scale)

    return pygame.transform.smoothscale(bg_raw, (bw, bh))

def draw_background(screen, background, player):
    sw, sh = SCREENSIZE
    bw, bh = background.get_size()

    max_x = bw - sw
    max_y = bh - sh

    parallax_x = 0.05
    parallax_y = 0.02

    dx = player.rect.centerx - player.start_pos[0]
    dy = player.rect.centery - player.start_pos[1]

    base_x = (sw - bw) / 2
    base_y = (sh - bh) / 2

    bg_x = base_x - dx * parallax_x
    bg_y = base_y - dy * parallax_y

    bg_x = max(sw - bw, min(0, bg_x))
    bg_y = max(sh - bh, min(0, bg_y))

    screen.blit(background, (bg_x, bg_y))

background = make_background(SCREENSIZE)

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
        self.start_time = None
    
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
            background = make_background(SCREENSIZE)
            cam.resize(SCREENSIZE)
            screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.RESIZABLE, vsync=1)

        #Menu input
        if state == "menu":

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                #Check of de instellingen knop is geklikt
                settings_knop = pygame.Rect(settings_rect.left - 6, settings_rect.top - 4,
                                            settings_rect.width + 12, settings_rect.height + 8)
                if settings_knop.collidepoint(event.pos):
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
                        
                        menu_page = level_id // LEVELS_PER_PAGE
                elif event.key == pygame.K_DOWN:
                     if level_id < len(level_files) - 1:
                        level_id += 1
                        huidig_level = f"levels/{level_files[level_id]}"
                        lvl_switch.play()

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
                        deaths = 0
                        reset_run_state(False)
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
                stopwatch.start()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state = "menu"
                    start_music('menu')
                elif event.key == pygame.K_t:
                    reset_run_state(False)
                    lowest = create_low_border()
                    reset_run_state(False)
                elif event.key == pygame.K_h:
                    if not active_hook:
                        active_hook = hook(player.rect.centerx, player.rect.centery, 10,10, gun.angle,30)
                    else:
                        player.derope()
                        active_hook = None


        elif state == "settings":

            cx = screen.get_width() // 2
            gap = 60
            start_y = 385

            #Knoppen voor de instellingen
            fs_rect = pygame.Rect(cx + 10, start_y, TOGGLE_W, TOGGLE_H)
            spd_rect = pygame.Rect(cx + 10, start_y + gap, TOGGLE_W, TOGGLE_H)
            dth_rect = pygame.Rect(cx + 10, start_y + gap * 2, TOGGLE_W, TOGGLE_H)

            #Volum slider
            slider = get_slider_rect(screen)

            #Home knop
            home_knop = pygame.Rect(
                homeknop_rect.left - 6,
                homeknop_rect.top - 4,
                homeknop_rect.width + 12,
                homeknop_rect.height + 8

            )

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if home_knop.collidepoint(event.pos):
                    state = "menu"  # Terug naar menu

                elif fs_rect.collidepoint(event.pos):
                    toggle_fullscreen()  # Zet fullscreen aan of uit
                    background = make_background(SCREENSIZE)

                elif spd_rect.collidepoint(event.pos):
                    show_speed = not show_speed  #Speed Laten zien of niet

                elif dth_rect.collidepoint(event.pos):
                    show_deaths = not show_deaths  #Deaths Laten zien of niet

                else:
                    slider_hitbox = pygame.Rect(slider.left, slider.top - 6, slider.width, slider.height + 12)
                    if slider_hitbox.collidepoint(event.pos):
                        slider_dragging = True
                        volume = int((event.pos[0] - slider.left) / slider.width * 100)
                        volume = max(0, min(100, volume))  #Houdt het volume tussen 0 en 100
                        pygame.mixer.music.set_volume(volume / 100)

            elif event.type == pygame.MOUSEBUTTONUP:
                slider_dragging = False  #Stop met verplaatsem van de slider

            elif event.type == pygame.MOUSEMOTION and slider_dragging:
                volume = int((event.pos[0] - slider.left) / slider.width * 100)
                volume = max(0, min(100, volume))  #Houd volume tussen 0 en 100
                pygame.mixer.music.set_volume(volume / 100)

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                state = "menu"  #Als je op escape drukt dan ga je terug naar het menu

    # draw en update
    if state == "menu":
        draw_menu(screen)


    elif state == "game":

        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(current_loop)
            pygame.mixer.music.play(-1)  #Start de muziek opnieuw als die niet speelt

        draw_background(screen, background, player)  #Teken de achtergrond
        cam.update_center(player.rect)  #Laat de camera de speler volgen
        player.update(blocks, gun)  #Update speler beweging en acties

        if player.rect.bottom > lowest + 300:
            reset_run_state(True)  #Reset als de speler van de map valt

        tile_function_update()

        if end_rect and player.rect.colliderect(end_rect):
            complete_time = stopwatch.get_formatted_time()  #Sla eindtijd op
            complete_deaths = deaths  #Sla deaths op
            level_times[level_id] = complete_time  #Bewaar tijd van dit level

            if level_id not in best_times or stopwatch.get_time() < time_to_seconds(best_times[level_id]):
                best_times[level_id] = complete_time  #Nieuwe beste tijd opslaan
                save_best_times(best_times)

            state = "level_complete"  #Ga naar level complete scherm

        gun.update(player, cam)  #Update het wapen

        if active_hook:
            active_hook.update(blocks, player, cam, screen)  #Update actieve hook
            active_hook.draw(screen, cam)  #Teken actieve hook

        vel_x = player.velx
        vel_y = player.vely

        speed = math.hypot(vel_x, vel_y)  #Absolute snelheid
        if speed < 1:
            speed = 0
        speed_pixels = round(speed, 2)  #Optioneel afronden

        if show_deaths: #Laat aantal deaths zien
            death_text = font_klein.render(f"Deaths: {deaths}", True, (200, 50, 50))
            screen.blit(death_text, (20, 20))

        if show_speed: #Laat snelheid zien
            speed_text = font_klein.render(f"Speed: {speed_pixels}", True, (0, 0, 0))
            screen.blit(speed_text, (20, screen.get_height() - 50))

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

    if state == "settings":
        draw_settings(screen)

    if state == "level_complete":
        draw_level_complete(screen)

    cam.update_shake()
    pygame.display.flip()
    clock.tick(FPS)
