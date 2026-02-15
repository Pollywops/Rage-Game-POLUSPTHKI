import pygame,sys
import json
import time
from camera import Camera
from player import Player
from gun import Gun
from hook import Hook

pygame.font.init()
pygame.mixer.init()

pygame.mixer.set_num_channels(40)
SCREENSIZE = [800,800]
FPS = 60
STATE = 'play'

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

screen = pygame.display.set_mode(SCREENSIZE,flags=pygame.RESIZABLE, vsync=1)
clock = pygame.time.Clock()

player_group = pygame.sprite.GroupSingle()
gun_group = pygame.sprite.GroupSingle()
blocks = pygame.sprite.Group()
buttons = pygame.sprite.Group()

# deze functie zet de lijnen uit het json bestand om in een matrix, zodat deze kan worden gebruikt om de blokken en de player te maken
def lines_to_matrix(lines):
    matrix = []
    for line in lines:
        line = line.strip()
        if line == "":
            continue
        matrix.append(line.split())
    return matrix

# deze functie laadt het level uit het json bestand, en zet het om in een matrix, zodat deze kan worden gebruikt om de blokken en de player te maken.
def load_from_json(path="level.json"):
    try:
        with open(path,"r",encoding="utf-8") as f:
            data = json.load(f)
        if "level" not in data:
            return None
        return lines_to_matrix(data["level"])
    except:
        return None

level = load_from_json()

# deze class maakt de blokken aan deze kunnen worden geupdate en getekend op het scherm
class Blocks(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,color):
        super().__init__()
        self.image = pygame.Surface((w,h))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (x , y)
    def update(self):
        pass
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

# hier zijn de player, gun, blocks, buttons en stopwatch aangemaakt, en de camera is ingesteld om te volgen op de player
cam = Camera(SCREENSIZE)

player_group.add(Player(500,0,50,50,BLUE))
player = player_group.sprite

gun_group.add(Gun(10,10))
gun = gun_group.sprite

blocks.add(Blocks(400,700,1000,100,GREEN))
blocks.add(Blocks(100,100,200,500,GREEN))

button1 = Button(500, 50, 175, 30, True, GREEN,
                 30, 5,fontoffsetY= -3,text= 'BULLETS:  ' + str(gun.bullets))
button2 = Button(500,100, 175, 30, True, GREEN,
                 30, 5,fontoffsetY= -3,text= 'BULLET TYPE: ' + str(gun.bullet_type))
stopwatch = Stopwatch()
stopwatch.start()

button3 = Button(500,150, 175, 30, True, GREEN,
                 30, 5,fontoffsetY= -3,text= 'TIME: 00:00.00')
hook = Hook()

buttons.add(button1)
buttons.add(button2)
buttons.add(button3)


# for y,i in enumerate(level):
#    for x,j in enumerate(i):
 #       if j == "X":
 #           blocks.add(Blocks(x*64,y*64,64,64,GREEN))
        # if j == "P":
        #     player.add(Player(x*64,y*64,50,50,BLUE))

# dit is de grote game loop, hier worden alle events afgehandeld, het scherm wordt geupdate en getekend.
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit() 

        if event.type == pygame.MOUSEBUTTONDOWN:
                gun.shoot(player)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                if gun.bullet_type == 'SUPER':
                    gun.bullet_type = 'NORMAL'
                    gun.bullets = 2
                else:
                    gun.bullet_type = 'SUPER'
                    gun.bullets = 2
                
            if event.key == pygame.K_SPACE:
                 stopwatch.reset()


        if event.type == pygame.VIDEORESIZE:
            SCREENSIZE = [event.w, event.h]
            cam.resize(SCREENSIZE)
            screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.RESIZABLE, vsync=1)

# hier worden alle sprites geupdate en getekend op het scherm, en de tijd wordt geupdate op de stopwatch
    screen.fill(WHITE)

    cam.update_center(player.rect)

    player.update(blocks, gun)
    gun.update(player, cam)
    hook.update(gun, blocks)

    for b in blocks:
        b.update()
        b.draw()

# hier worden de knoppen geupdate en getekend op het scherm, en de tekst wordt geupdate met de huidige hoeveelheid kogels, het type kogel en de tijd op de stopwatch
    button1.text = 'BULLETS: ' + str(gun.bullets)
    button2.text = 'BULLET TYPE: ' + str(gun.bullet_type)
    button3.text = 'TIME: ' + stopwatch.get_formatted_time()
    for b in buttons:
        b.update()
        b.draw()


    gun.draw(screen, cam)
    player.draw(screen, cam)
    hook.draw(screen, cam)

    pygame.display.flip()

    clock.tick(FPS)
