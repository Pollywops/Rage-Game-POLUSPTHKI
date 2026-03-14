import pygame, sys, json, os, subprocess
import time

pygame.init()
pygame.font.init()

SCREENSIZE = (800, 600)
FPS = 60
GRID = 32
EMPTY = 0

WHITE = (200, 200, 200)
BLACK = (30, 30, 30)
ORANGE = (252, 76, 2)
RED = (255, 0, 0)
BLUE = (0, 120, 255)

screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.RESIZABLE, vsync=1)
clock = pygame.time.Clock()

with open("tiledata.json", "r", encoding="utf-8") as file:
    tiledata = json.load(file)

tile_defs = tiledata["tiles"]
tile_surfaces = []
tile_names = []

for tile in tile_defs:
    image = pygame.image.load(os.path.join("textures", tile["file"])).convert_alpha()
    image = pygame.transform.scale(image, (GRID, GRID))
    tile_surfaces.append(image)
    tile_names.append(tile["name"])

placed = {}
history = []
markers = {"spawn": None, "end": None}

cam_x = 0
cam_y = 0
scroll_speed = 8
selected_tile = 0
current_level = 1
MAX_LEVEL = 20

title_font = pygame.font.SysFont("Arial", 24)
small_font = pygame.font.SysFont("Arial", 18)
menu_font = pygame.font.SysFont("Arial", 24)

def level_path(level_id):
    return f"levels/level{level_id}.json"

def go_to_menu():
    save_level()
    main = subprocess.Popen([sys.executable, "main.py"])
    time.sleep(1)
    if main.poll() == None:
        pygame.quit()
        sys.exit()

def get_menu_button_rect():
    text = menu_font.render("Menu", True, BLACK)
    rect = text.get_rect(topright=(screen.get_width() - 20, 20))
    button_rect = pygame.Rect(rect.left - 10, rect.top - 6, rect.width + 20, rect.height + 12)
    return button_rect, text, rect

def save_level():
    if placed:
        min_x = min(x for x, y in placed)
        max_x = max(x for x, y in placed)
        min_y = min(y for x, y in placed)
        max_y = max(y for x, y in placed)
    else:
        min_x = max_x = min_y = max_y = 0

    width = max_x - min_x + 1
    height = max_y - min_y + 1

    matrix = [[EMPTY for _ in range(width)] for _ in range(height)]

    for (x, y), tile_id in placed.items():
        matrix[y - min_y][x - min_x] = tile_id + 1

    data = {
        "level": matrix,
        "spawn": [markers["spawn"][0] - min_x, markers["spawn"][1] - min_y] if markers["spawn"] else None,
        "end": [markers["end"][0] - min_x, markers["end"][1] - min_y] if markers["end"] else None,
        "offset": [min_x, min_y]
    }

    with open(level_path(current_level), "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

def load_level(level_id):
    global current_level
    current_level = level_id
    placed.clear()
    history.clear()
    markers["spawn"] = None
    markers["end"] = None

    path = level_path(level_id)
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    matrix = data.get("level", [])
    offset = data.get("offset", [0, 0])
    off_x, off_y = offset

    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if val != EMPTY:
                placed[(x + off_x, y + off_y)] = int(val) - 1

    spawn = data.get("spawn")
    end = data.get("end")

    if spawn:
        markers["spawn"] = [spawn[0] + off_x, spawn[1] + off_y]
    if end:
        markers["end"] = [end[0] + off_x, end[1] + off_y]

def clear_level():
    placed.clear()
    history.clear()
    markers["spawn"] = None
    markers["end"] = None

def screen_to_grid(mx, my):
    return (mx + cam_x) // GRID, (my + cam_y) // GRID

def draw_marker(pos, color):
    if pos is None:
        return
    gx, gy = pos
    rect = pygame.Rect(gx * GRID - cam_x, gy * GRID - cam_y, GRID, GRID)
    pygame.draw.rect(screen, color, rect, 3)

def draw_menu_button():
    button_rect, text, text_rect = get_menu_button_rect()
    pygame.draw.rect(screen, WHITE, button_rect)
    pygame.draw.rect(screen, BLACK, button_rect, 2)
    screen.blit(text, text_rect)

load_level(current_level)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.VIDEORESIZE:
            SCREENSIZE = (event.w, event.h)
            screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.RESIZABLE, vsync=1)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            menu_button_rect, _, _ = get_menu_button_rect()
            if event.button == 1 and menu_button_rect.collidepoint(event.pos):
                go_to_menu()

            gx, gy = screen_to_grid(mx, my)

            if event.button == 1:
                placed[(gx, gy)] = selected_tile
                history.append((gx, gy))
            elif event.button == 3:
                placed.pop((gx, gy), None)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                go_to_menu()

            elif event.key == pygame.K_1:
                selected_tile = (selected_tile + 1) % len(tile_surfaces)

            elif event.key == pygame.K_s:
                save_level()

            elif event.key == pygame.K_EQUALS:
                save_level()
                current_level += 1
                if current_level > MAX_LEVEL:
                    current_level = 1
                load_level(current_level)

            elif event.key == pygame.K_MINUS:
                save_level()
                current_level -= 1
                if current_level < 1:
                    current_level = MAX_LEVEL
                load_level(current_level)

            elif event.key == pygame.K_z:
                if history:
                    last = history.pop()
                    placed.pop(last, None)

            elif event.key == pygame.K_b:
                markers["spawn"] = list(screen_to_grid(*pygame.mouse.get_pos()))

            elif event.key == pygame.K_e:
                markers["end"] = list(screen_to_grid(*pygame.mouse.get_pos()))

            elif event.key == pygame.K_c:
                clear_level()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        cam_x -= scroll_speed
    if keys[pygame.K_RIGHT]:
        cam_x += scroll_speed
    if keys[pygame.K_UP]:
        cam_y -= scroll_speed
    if keys[pygame.K_DOWN]:
        cam_y += scroll_speed

    screen.fill(WHITE)

    for (gx, gy), tile_id in placed.items():
        screen.blit(tile_surfaces[tile_id], (gx * GRID - cam_x, gy * GRID - cam_y))

    startx = -(cam_x % GRID)
    starty = -(cam_y % GRID)

    for x in range(startx, screen.get_width(), GRID):
        pygame.draw.line(screen, BLACK, (x, 0), (x, screen.get_height()))
    for y in range(starty, screen.get_height(), GRID):
        pygame.draw.line(screen, BLACK, (0, y), (screen.get_width(), y))

    screen.blit(title_font.render(f"geselecteerd: {tile_names[selected_tile]}", True, BLACK), (10, 10))
    screen.blit(title_font.render(f"level: {current_level} (-/+)", True, BLACK), (10, 36))

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

    draw_marker(markers["spawn"], RED)
    draw_marker(markers["end"], BLUE)
    draw_menu_button()

    pygame.display.flip()
    clock.tick(FPS)
