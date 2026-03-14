
import pygame, sys, json, os, subprocess
import time

pygame.init()
pygame.font.init()

SCREENSIZE = (800, 600)  #Grootte van het scherm
FPS = 60                 #Frames per seconde
GRID = 32                #Grootte van één vakje in het raster
EMPTY = 0                #Waarde voor een lege tile

#Kleuren
WHITE = (200, 200, 200)
BLACK = (30, 30, 30)
ORANGE = (252, 76, 2)
RED = (255, 0, 0)
BLUE = (0, 120, 255)

screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.RESIZABLE, vsync=1)
clock = pygame.time.Clock()  #Klok voor de FPS

file = open("tiledata.json", "r", encoding="utf-8")
tiledata = json.load(file)   #Leest de tiledata uit het JSON-bestand
file.close()

tile_defs = tiledata["tiles"]  #Pakt de lijst met tiles
tile_surfaces = []             #Lijst met tile afbeeldingen
tile_names = []                #Lijst met tile namen

for tile in tile_defs:
    image = pygame.image.load(os.path.join("textures", tile["file"])).convert_alpha()
    image = pygame.transform.scale(image, (GRID, GRID))  #Schaalt de afbeelding naar grid grootte
    tile_surfaces.append(image)                          #Slaat de afbeelding op
    tile_names.append(tile["name"])                     #Slaat de naam van de tile op

placed = {}  #Bewaart welke tiles waar geplaatst zijn
history = []  #Houdt geplaatste tiles bij voor undo
markers = {"spawn": None, "end": None}  #Begin en eindpunt van het level

cam_x = 0
cam_y = 0
scroll_speed = 8   #Snelheid waarmee de camera beweegt
selected_tile = 0  #Geselecteerde tile
current_level = 1  #Huidig level
MAX_LEVEL = 20     #Hoogste levelnummer

title_font = pygame.font.SysFont("Arial", 24)
small_font = pygame.font.SysFont("Arial", 18)
menu_font = pygame.font.SysFont("Arial", 24)

def level_path(level_id):
    return f"levels/level{level_id}.json"  # Geeft het pad van het levelbestand terug


def go_to_menu():
    save_level()  #Slaat het huidige level eerst op
    main = subprocess.Popen([sys.executable, "main.py"])  # Start main.py
    time.sleep(2)  #Wacht even zodat main.py kan opstarten

    if main.poll() == None:
        pygame.quit()
        sys.exit()  #Sluit deze editor af als main.py nog draait


def get_menu_button_rect():
    text = menu_font.render("Menu", True, BLACK)  #Maakt de tekst van de menu-knop
    rect = text.get_rect(topright=(screen.get_width() - 20, 20))  #Positie van de tekst
    button_rect = pygame.Rect(rect.left - 10, rect.top - 6, rect.width + 20, rect.height + 12)
    return button_rect, text, rect  #Geeft knop rect, tekst en tekst rect terug


def save_level():
    if placed:
        min_x = min(x for x, y in placed)
        max_x = max(x for x, y in placed)
        min_y = min(y for x, y in placed)
        max_y = max(y for x, y in placed)
        #Zoekt de buitenste randen van alle geplaatste tiles
    else:
        min_x = max_x = min_y = max_y = 0  #Als er niks staat, gebruik 0

    width = max_x - min_x + 1
    height = max_y - min_y + 1  #Breedte en hoogte van het level

    matrix = [[EMPTY for _ in range(width)] for _ in range(height)]
    #Maakt een lege matrix voor het level

    for (x, y), tile_id in placed.items():
        matrix[y - min_y][x - min_x] = tile_id + 1
        #Zet alle geplaatste tiles in de matrix

    data = {
        "level": matrix,
        "spawn": [markers["spawn"][0] - min_x, markers["spawn"][1] - min_y] if markers["spawn"] else None,
        "end": [markers["end"][0] - min_x, markers["end"][1] - min_y] if markers["end"] else None,
        "offset": [min_x, min_y]
    }
    #Slaat ook beginpunt, eindpunt en offset op

    file = open(level_path(current_level), "w", encoding="utf-8")
    json.dump(data, file, indent=2)  #Schrijft het level naar JSON
    file.close()


def load_level(level_id):
    global current_level
    current_level = level_id  #Zet het huidige levelnummer
    placed.clear()
    history.clear()
    markers["spawn"] = None
    markers["end"] = None
    #Maakt eerst het huidige level leeg

    path = level_path(level_id)
    if not os.path.exists(path):
        return  #Stop als het bestand niet bestaat

    file = open(path, "r", encoding="utf-8")
    data = json.load(file)  #Leest het levelbestand in
    file.close()

    matrix = data.get("level", [])
    offset = data.get("offset", [0, 0])
    off_x, off_y = offset

    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if val != EMPTY:
                placed[(x + off_x, y + off_y)] = int(val) - 1
                #Zet alle tiles weer terug op hun plek

    spawn = data.get("spawn")
    end = data.get("end")

    if spawn:
        markers["spawn"] = [spawn[0] + off_x, spawn[1] + off_y]  #Zet het spawnpunt op de juiste plek
    if end:
        markers["end"] = [end[0] + off_x, end[1] + off_y]  #Zet het eindpunt op de juiste plek


def clear_level():
    placed.clear()
    history.clear()
    markers["spawn"] = None
    markers["end"] = None
    #Maakt alle geplaatste tiles en markers leeg


def screen_to_grid(mx, my):
    return (mx + cam_x) // GRID, (my + cam_y) // GRID
    #Zet schermcoördinaten om naar gridcoördinaten


def draw_marker(pos, color):
    if pos is None:
        return  #Teken niks als er geen marker is

    gx, gy = pos
    rect = pygame.Rect(gx * GRID - cam_x, gy * GRID - cam_y, GRID, GRID)
    pygame.draw.rect(screen, color, rect, 3)  #Tekent een gekleurde rand om de marker

def draw_menu_button():
    button_rect, text, text_rect = get_menu_button_rect()
    pygame.draw.rect(screen, WHITE, button_rect)  #Tekent de knopachtergrond
    pygame.draw.rect(screen, BLACK, button_rect, 2)  #Tekent de rand van de knop
    screen.blit(text, text_rect)  #Tekent de tekst op de knop

load_level(current_level)  #Laadt het huidige level bij het opstarten

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()  #Sluit het programma af

        if event.type == pygame.VIDEORESIZE:
            SCREENSIZE = (event.w, event.h)
            screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.RESIZABLE, vsync=1)
            #Past het scherm aan als het venster van grootte verandert

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos  #Muispositie

            menu_button_rect, _, _ = get_menu_button_rect()
            if event.button == 1 and menu_button_rect.collidepoint(event.pos):
                go_to_menu()  #Ga terug naar het menu als op de knop is geklikt

            gx, gy = screen_to_grid(mx, my)  #Zet schermpositie om naar gridpositie

            if event.button == 1:
                placed[(gx, gy)] = selected_tile
                history.append((gx, gy))  #Plaatst een tile en slaat die op voor undo

            elif event.button == 3:
                placed.pop((gx, gy), None)  #Verwijdert een tile met rechtermuisknop

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                go_to_menu()  #Ga terug naar het menu

            elif event.key == pygame.K_1:
                selected_tile = (selected_tile + 1) % len(tile_surfaces)
                #Kies de volgende tile

            elif event.key == pygame.K_s:
                save_level()  #Sla het level op

            elif event.key == pygame.K_EQUALS:
                save_level()
                current_level += 1
                if current_level > MAX_LEVEL:
                    current_level = 1
                load_level(current_level)  #Ga naar het volgende level

            elif event.key == pygame.K_MINUS:
                save_level()
                current_level -= 1
                if current_level < 1:
                    current_level = MAX_LEVEL
                load_level(current_level)  #Ga naar het vorige level

            elif event.key == pygame.K_z:
                if history:
                    last = history.pop()
                    placed.pop(last, None)  #Maakt de laatste geplaatste tile ongedaan

            elif event.key == pygame.K_b:
                markers["spawn"] = list(screen_to_grid(*pygame.mouse.get_pos()))
                #Zet beginpunt op de huidige muispositie

            elif event.key == pygame.K_e:
                markers["end"] = list(screen_to_grid(*pygame.mouse.get_pos()))
                #Zet eindpunt op de huidige muispositie

            elif event.key == pygame.K_c:
                clear_level()  #Maakt het level leeg

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        cam_x -= scroll_speed  #Beweeg camera naar links
    if keys[pygame.K_RIGHT]:
        cam_x += scroll_speed  #Beweeg camera naar rechts
    if keys[pygame.K_UP]:
        cam_y -= scroll_speed  #Beweeg camera omhoog
    if keys[pygame.K_DOWN]:
        cam_y += scroll_speed  #Beweeg camera omlaag

    screen.fill(WHITE)  #Maakt de achtergrond wit

    for (gx, gy), tile_id in placed.items():
        screen.blit(tile_surfaces[tile_id], (gx * GRID - cam_x, gy * GRID - cam_y))
        #Tekent alle geplaatste tiles

    startx = -(cam_x % GRID)
    starty = -(cam_y % GRID)

    for x in range(startx, screen.get_width(), GRID):
        pygame.draw.line(screen, BLACK, (x, 0), (x, screen.get_height()))
    for y in range(starty, screen.get_height(), GRID):
        pygame.draw.line(screen, BLACK, (0, y), (screen.get_width(), y))
    #Tekent het raster

    screen.blit(title_font.render(f"geselecteerd: {tile_names[selected_tile]}", True, BLACK), (10, 10))
    screen.blit(title_font.render(f"level: {current_level} (-/+)", True, BLACK), (10, 36))
    #Laat zien welke tile en welk level geselecteerd is

    controls = [
        "LMB: plaats",
        "RMB: verwijder",
        "Z: undo",
        "1: volgende tile",
        "S: save",
        "B: begin",
        "E: einde",
        "C: clear level",
        "Arrows: bewegen",
        "ESC/Menu: terug naar main menu",
    ]
    for i, line in enumerate(controls):
        screen.blit(small_font.render(line, True, BLACK), (10, 100 + i * 30))
        #Tekent de besturingsteksten

    draw_marker(markers["spawn"], RED)   #Tekent spawn marker
    draw_marker(markers["end"], BLUE)    #Tekent eind marker
    draw_menu_button()                   #Tekent menu knop

    pygame.display.flip()  #Vernieuwt het scherm
    clock.tick(FPS)        #Houdt de game op de juiste FPS
