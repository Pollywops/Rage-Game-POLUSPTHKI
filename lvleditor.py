import pygame,sys,math,json,os

# dit is de level editor, hier kan je levels maken en opslaan in een json bestand. Je kan ook levels laden vanuit een json bestand. 
# De levels worden opgeslagen als een matrix van strings, waarbij elke string een type blok vertegenwoordigt. De textures voor de blokken worden geladen uit de textures map. 
# Je kan blokken plaatsen door te klikken op het scherm, en je kan blokken verwijderen door op z te drukken. 
# Je kan ook scrollen door het scherm met de pijltjestoetsen.
pygame.font.init()

SCREENSIZE = [800,800]
FPS = 60

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

grid_size = 32

screen = pygame.display.set_mode(SCREENSIZE,flags=pygame.SCALED, vsync=1)
clock = pygame.time.Clock()

blocks = pygame.sprite.Group()

offsetx = 0
offsety = 0
scroll_speed = 8

selected_block = 0

blockorder = []

files = sorted([f for f in os.listdir('textures') if f.lower().endswith('.png')])
textures = [os.path.join("textures", f) for f in files]

# preload surfaces
tile_surfaces = [
    pygame.transform.scale(pygame.image.load(p).convert_alpha(), (grid_size, grid_size))
    for p in textures
]

placed = {}  # (gx,gy) -> Blocks sprite


tile_map = {}
EMPTY = 0

# textures = ['textures/Aarde_Links','textures/Aarde_Midden.png','textures/Aarde_rechts.png','textures/Grasblok.png'
#             ]


class Blocks(pygame.sprite.Sprite):
    def __init__(self, x, y, gx, gy, tile_id):
        super().__init__()
        self.image = tile_surfaces[tile_id]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.gridx = gx
        self.gridy = gy
        self.type = tile_id  # blijft je ID

    def update(self, offsetx, offsety):
        screen.blit(self.image, (self.rect.x - offsetx, self.rect.y - offsety))


    def update(self,offsetx,offsety):
        screen.blit(self.image, (self.rect.x-offsetx,self.rect.y-offsety))

def save_to_json(matrix):
    with open('levels/level.json', "w", encoding="utf-8") as f:
        json.dump({"level": matrix}, f, indent=2)

def load_from_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        lvl = data.get("level")
        return lvl  # verwacht list-of-lists met ints
    except Exception as e:
        return None


tiledata = load_from_json("tiledata.json")

def build_blocks_from_matrix(matrix):
    placed.clear()
    blocks.empty()
    blockorder.clear()

    if matrix is None:
        return

    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if val == EMPTY:
                continue

            tile_id = int(val) - 1  # <-- belangrijk
            if 0 <= tile_id < len(tile_surfaces):
                b = Blocks(x * grid_size, y * grid_size, x, y, tile_id)
                blocks.add(b)
                placed[(x, y)] = b
                blockorder.append(b)


def make_matrix():
    max_x, max_y = find_matrix_size()
    return [[EMPTY for _ in range(max_x + 1)] for _ in range(max_y + 1)]

def find_matrix_size():
    if not placed:
        return [0, 0]
    max_x = max(gx for gx, _ in placed.keys())
    max_y = max(gy for _, gy in placed.keys())
    return [max_x, max_y]

def save_lvl(matrix):
    for (gx, gy), block in placed.items():
        matrix[gy][gx] = block.type + 1  # <-- belangrijk
    return matrix

def print_lvl(matrix):
    for row in matrix:
        print(" ".join(map(str, row)))
    print()

def set_tile(gx, gy, tile_id):
    key = (gx, gy)
    old = placed.get(key)

    # als dezelfde tile er al staat: niks doen
    if old and old.type == tile_id:
        return

    # oude tile eruit (geen overlap!)
    if old:
        blocks.remove(old)
        try:
            blockorder.remove(old)
        except ValueError:
            pass

    b = Blocks(gx * grid_size, gy * grid_size, gx, gy, tile_id)
    blocks.add(b)
    placed[key] = b
    blockorder.append(b)

def erase_tile(gx, gy):
    key = (gx, gy)
    old = placed.pop(key, None)
    if old:
        blocks.remove(old)
        try:
            blockorder.remove(old)
        except ValueError:
            pass


tiledata = load_from_json("tiledata.json")

loaded = load_from_json("levels/level.json")
build_blocks_from_matrix(loaded)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            mousepos = pygame.mouse.get_pos()
            gen_mousepos = (mousepos[0] + offsetx, mousepos[1] + offsety)
            gridx, gridy = gen_mousepos[0] // grid_size, gen_mousepos[1] // grid_size

            if event.button == 1:  # left click
                set_tile(gridx, gridy, selected_block)
            elif event.button == 3:  # right click
                erase_tile(gridx, gridy)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z:
                if blockorder:
                    last = blockorder.pop()
                    blocks.remove(last)
                    placed.pop((last.gridx, last.gridy), None)

            if event.key == pygame.K_1:
                selected_block = (selected_block + 1) % len(textures)

            if event.key == pygame.K_s:
                lvl = make_matrix()
                lvl = save_lvl(lvl)
                print_lvl(lvl)
                save_to_json(lvl)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT]:
        if offsetx - scroll_speed < 0:
            offsetx = 0
        else:
            offsetx -= scroll_speed
    if keys[pygame.K_LEFT]:
        offsetx += scroll_speed
    if keys[pygame.K_UP]:
        if offsety - scroll_speed < 0:
            offsety = 0
        else:
            offsety -= scroll_speed
    if keys[pygame.K_DOWN]:
        offsety += scroll_speed

    screen.fill(WHITE)
    blocks.update(offsetx,offsety)

    startx = -(offsetx%grid_size)
    starty = -(offsety%grid_size)

    for x in range(startx,SCREENSIZE[0],grid_size):
        pygame.draw.line(screen,BLACK,(x,0),(x,SCREENSIZE[1]))

    for y in range(starty,SCREENSIZE[1],grid_size):
        pygame.draw.line(screen,BLACK,(0,y),(SCREENSIZE[0],y))

    pygame.display.flip()
    clock.tick(FPS)
