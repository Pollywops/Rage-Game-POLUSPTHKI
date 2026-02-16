import pygame,sys
import json
import time
import math
from camera import Camera
from player import Player
from gun import Gun
from hook import Hook

# VARIABLES

pygame.font.init()
pygame.mixer.init()

font = pygame.font.SysFont("Arial", 72)
small_font = pygame.font.SysFont("Arial", 36)

pygame.mixer.set_num_channels(40)
SCREENSIZE = [800,800]
FPS = 60
pygame.font.get_fonts()
state = "menu"  

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

# FUNCTIONS

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

def draw_menu(screen):
    screen.fill((255, 255, 255))

    title = font.render("Rage Game", True, (0, 0, 0))
    hint1 = small_font.render("ENTER = Play", True, (0, 0, 0))
    hint2 = small_font.render("ESC = Quit", True, (0, 0, 0))

    screen.blit(title, title.get_rect(center=(screen.get_width()//2, 250)))
    screen.blit(hint1, hint1.get_rect(center=(screen.get_width()//2, 360)))
    screen.blit(hint2, hint2.get_rect(center=(screen.get_width()//2, 410)))

level = load_from_json()

#CLASSES

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

class Projectile(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = None
        self.transformed_image = None
        # self.rect = None
        # # self.rect.centerx = None
        # self.rect.centery = None
        self.angle = None
        self.speed = None
    def start(self, x, y, w ,h, angle, speed):
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



#VARIABLES 2


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
# hook = Hook()
# pro1 = Projectile()

buttons.add(button1)
buttons.add(button2)
buttons.add(button3)


# for y,i in enumerate(level):
#    for x,j in enumerate(i):
 #       if j == "X":
 #           blocks.add(Blocks(x*64,y*64,64,64,GREEN))
        # if j == "P":
        #     player.add(Player(x*64,y*64,50,50,BLUE))

#WHILE LOOP

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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    player.reset_position()
                    stopwatch.reset()
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
                        gun.bullets = 2
                        print("NORMAL BULLET ACTIVATED")
                    else:
                        gun.bullet_type = 'SUPER'
                        gun.bullets = 2
                        print("SUPER BULLET ACTIVATED")
                elif event.key == pygame.K_t:
                    stopwatch.reset()
                    player.reset_position()
                elif event.key == pygame.K_h:
                    hook.hook()

    # Updat en draw
    if state == "menu":
        draw_menu(screen)

    elif state == "game":
        screen.fill(WHITE)

        cam.update_center(player.rect)

        player.update(blocks, gun)
        gun.update(player, cam)
        # hook.update(gun, pro1)

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
        # hook.draw(screen, cam)

    pygame.display.flip()
    clock.tick(FPS)