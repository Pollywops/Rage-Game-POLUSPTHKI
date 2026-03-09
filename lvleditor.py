import pygame, sys, json, os

pygame.init()
pygame.font.init()

SCREENSIZE = (800, 800)
FPS = 60
GRID = 32
EMPTY = 0

WHITE = (200, 200, 200)
BLACK = (30, 30, 30)
ORANGE = (252, 76, 2)
RED = (255, 0, 0)
BLUE = (0, 120, 255)

screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.SCALED, vsync=1)
clock = pygame.time.Clock()

with open("tiledata.json", "r", encoding="utf-8") as f:
    tiledata = json.load(f)

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

def level_path(level_id):
    return f"levels/level{level_id}.json"

def save_level():
    if placed:
        max_x = max(x for x, y in placed)
        max_y = max(y for x, y in placed)
    else:
        max_x = max_y = 0

    matrix = [[EMPTY for _ in range(max_x + 1)] for _ in range(max_y + 1)]

    for (x, y), tile_id in placed.items():
        matrix[y][x] = tile_id + 1

    data = {
        "level": matrix,
        "spawn": markers["spawn"],
        "end": markers["end"]
    }

    with open(level_path(current_level), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

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

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    matrix = data.get("level", [])
    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if val != EMPTY:
                placed[(x, y)] = int(val) - 1

    markers["spawn"] = data.get("spawn")
    markers["end"] = data.get("end")

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

load_level(current_level)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            gx, gy = screen_to_grid(mx, my)

            clear_rect = pygame.Rect(screen.get_width() - 170, 10, 160, 34)
            if event.button == 1 and clear_rect.collidepoint(event.pos):
                clear_level()
                continue

            if event.button == 1:
                placed[(gx, gy)] = selected_tile
                history.append((gx, gy))
            elif event.button == 3:
                placed.pop((gx, gy), None)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                selected_tile = (selected_tile + 1) % len(tile_surfaces)

            elif event.key == pygame.K_s:
                save_level()

            elif event.key == pygame.K_n:
                save_level()
                current_level += 1
                if current_level > MAX_LEVEL:
                    current_level = 1
                load_level(current_level)

            elif event.key == pygame.K_m:
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

    clear_rect = pygame.Rect(screen.get_width() - 170, 10, 160, 34)
    pygame.draw.rect(screen, ORANGE, clear_rect)
    pygame.draw.rect(screen, BLACK, clear_rect, 2)
    clear_text = small_font.render("CLEAR ALL", True, BLACK)
    screen.blit(clear_text, clear_text.get_rect(center=clear_rect.center))

    screen.blit(title_font.render(f"Selected: {tile_names[selected_tile]}", True, BLACK), (10, 10))
    screen.blit(title_font.render(f"Editing Level: {current_level} (N/M)", True, BLACK), (10, 36))

    controls = [
        "LMB: place",
        "RMB: erase",
        "Z: undo",
        "1: next tile",
        "S: save",
        "N/M: next/prev level",
        "B: spawn",
        "E: end",
        "Arrow keys: scroll",
    ]
    for i, line in enumerate(controls):
        screen.blit(small_font.render(line, True, BLACK), (10, 66 + i * 20))

    draw_marker(markers["spawn"], RED)
    draw_marker(markers["end"], BLUE)

    pygame.display.flip()
    clock.tick(FPS)