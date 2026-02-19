import pygame,sys,math,json,os

# dit is de level editor, hier kan je levels maken en opslaan in een json bestand. Je kan ook levels laden vanuit een json bestand. 
# De levels worden opgeslagen als een matrix van strings, waarbij elke string een type blok vertegenwoordigt. De textures voor de blokken worden geladen uit de textures map. 
# Je kan blokken plaatsen door te klikken op het scherm, en je kan blokken verwijderen door op z te drukken. 
# Je kan ook scrollen door het scherm met de pijltjestoetsen.
pygame.init()
pygame.font.init()
pygame.mixer.set_num_channels(40)
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

tile_map = {}

# textures = ['textures/Aarde_Links','textures/Aarde_Midden.png','textures/Aarde_rechts.png','textures/Grasblok.png'
#             ]


class Blocks(pygame.sprite.Sprite):
    def __init__(self,x,y,gx,gy,w,h,tex,type,color):
        super().__init__()
 
        self.texture = pygame.image.load(tex)
        self.image = pygame.transform.scale(self.texture,(w,h))

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.gridx = gx
        self.gridy = gy
        self.type = type

    def update(self,offsetx,offsety):
        screen.blit(self.image, (self.rect.x-offsetx,self.rect.y-offsety))

def find_matrix_size():
    if len(blocks.sprites()) == 0:
        return [0,0]
    max_x = 0
    max_y = 0
    for i in blocks.sprites():
        if i.gridx > max_x:
            max_x = i.gridx
        if i.gridy > max_y:
            max_y = i.gridy
    return [max_x,max_y]

def make_matrix():
    matrix = []
    for y in range(find_matrix_size()[1]+1):
        row = []
        for x in range(find_matrix_size()[0]+1):
            row.append(" ")
        matrix.append(row)
    return matrix

def save_lvl(matrix):
    for block in blocks.sprites():
        matrix[block.gridy][block.gridx] = f"{block.type}"
    return matrix




def save_to_json(matrix, path="level.json"):
    data = {"level": matrix}
    with open(path,"w",encoding="utf-8") as f:
        json.dump(data,f,separators=(",",":"),indent=2)
    



def load_from_json(path="level.json"):
    try:
        with open(path,"r",encoding="utf-8") as f:
            data = json.load(f)
        if "level" not in data:
            return None
        return data["level"]
    except:
        return None



tiledata = load_from_json("tiledata.json")

def build_blocks_from_matrix(matrix):
    if matrix is None:
        return
    blocks.empty()
    blockorder.clear()

    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if val == " ":
                continue

            # accepteer alleen digits
            if isinstance(val, str) and not val.isdigit():
                continue

            tile_id = int(val)
            if tile_id < 0 or tile_id >= len(textures):
                continue

            b = Blocks(x*grid_size, y*grid_size, x, y,
                       grid_size, grid_size, textures[tile_id], tile_id, GREEN)
            blocks.add(b)
            blockorder.append(b)


def print_lvl(matrix):
    for row in matrix: 
        print(" ".join(row))
    print()

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
            gen_mousepos = (mousepos[0]+offsetx,mousepos[1]+offsety)
            gridx,gridy = gen_mousepos[0]//grid_size,gen_mousepos[1]//grid_size
            b = Blocks(gridx*grid_size,gridy*grid_size,gridx,gridy,grid_size,grid_size,textures[selected_block],selected_block,GREEN)
            blocks.add(b)
            blockorder.append(b)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z:
                if len(blockorder) > 0:
                    blocks.remove(blockorder.pop())
                    
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
