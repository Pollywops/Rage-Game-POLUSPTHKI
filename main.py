import pygame,sys,math


pygame.font.init()
pygame.mixer.init()

shotgun_shot = pygame.mixer.Sound('sounds/Shotgun_shot.mp3')
shotgun_empty = pygame.mixer.Sound('sounds/Empty.mp3')

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

player = pygame.sprite.GroupSingle()
gun = pygame.sprite.GroupSingle()
blocks = pygame.sprite.Group()


def lines_to_matrix(lines):
    matrix = []
    for line in lines:
        line = line.strip()
        if line == "":
            continue
        matrix.append(line.split())
    return matrix


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



class Player(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,color):
        super().__init__()
        self.realimage = pygame.image.load('textures/Pot.png').convert_alpha()
        self.originalimage = pygame.transform.scale(self.realimage,(60,60))
        self.image = self.originalimage
        self.rect = self.image.get_rect()
        self.rect.center = x,y
        
        self.centerx = x
        self.centery = y
        self.velx = 0
        self.vely = 0
        self.touchingground = False
        self.wasgrounded = False
        self.touchingwall = False
        self.touchingceiling = False
        self.friction = 1
     
     
    def add_vel(self,x,y):
        self.velx += x
        self.vely += y
     
        
    def physics(self):
        self.touchingground = False
        self.touchingwall = False
        self.touchingceiling = False

        self.vely += 0.4
        self.friction = 1

        self.rect.centerx += self.velx
        for sprite in pygame.sprite.spritecollide(self,blocks,False):
            if self.rect.colliderect(sprite.rect):
                if self.velx > 0:
                    self.rect.right = sprite.rect.left
                    self.velx = 0
                elif self.velx < 0:
                    self.rect.left = sprite.rect.right
                    self.velx = 0
            gun.sprite.bullets = 2
        self.rect.centery += self.vely
        for sprite in pygame.sprite.spritecollide(self,blocks,False):
            if self.rect.colliderect(sprite.rect):
                if self.vely > 0:
                    self.rect.bottom = sprite.rect.top
                    self.vely = 0
                    self.touchingground = True
                    self.friction = 30
                    #print(self.friction)
                elif self.vely < 0:
                    self.rect.top = sprite.rect.bottom
                    self.vely = 0
                    self.touchingceiling = True
                    self.friction = 30
                    #print(self.friction)
            gun.sprite.bullets = 2

        if self.velx > 0:
            if self.velx <= 0.03:
                self.velx = 0

            else:
                self.velx -= 0.03 * self.friction
                if self.velx <= 0.03:
                    self.velx = 0
        if self.velx < 0:
            if self.velx >= 0.03:
                self.velx = 0

            else:
                self.velx += 0.03 * self.friction
                if self.velx >= 0.03:
                    self.velx = 0
  
    def update(self):
        keys = pygame.key.get_pressed()
        
        #handeling deacaleration

        # if keys[pygame.K_w]:
        #     self.vely = -5
                
            
        # elif keys[pygame.K_s]:
        #     self.vely = 5
        
      
                
        if keys[pygame.K_d]:
            self.velx = 5
        
        elif keys[pygame.K_a]:
            self.velx = -5





        self.physics()

        screen.blit(self.image,[self.rect.left - self.rect.centerx + SCREENSIZE[0]/2,self.rect.top - self.rect.centery + SCREENSIZE[1]/2])
    
        
class Gun(pygame.sprite.Sprite):
    def __init__(self,w,h):
        super().__init__()
        self.realimage = pygame.image.load('textures/Shotgun.png').convert_alpha()
        self.original_image = pygame.transform.scale(self.realimage,(128,128))
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.center = (10,10)
        self.flipped = False
        self.bullets = 2
    
    def shoot(self):
        self.bullets = self.bullets - 1
        #print(self.bullets)
        if self.bullets >= 0:
            shotgun_shot.play()
            if player.sprite.vely > 0:
                player.sprite.vely = 0
                print(player.sprite.vely)
            addvelx = -math.cos(self.angle)*10
            addvely = -math.sin(self.angle)*10
            player.sprite.add_vel(addvelx,addvely)
        else:
            shotgun_empty.play()
    
      
    def update(self,px,py):
        mx = pygame.mouse.get_pos()[0] + player.sprite.rect.centerx - SCREENSIZE[0] / 2
        my = pygame.mouse.get_pos()[1] + player.sprite.rect.centery - SCREENSIZE[1] / 2
        self.angle = math.atan2(my-py,mx-px)
        #print(f'x:{math.cos(self.angle)}, y:{math.sin(self.angle)}')

        pos = ((px + math.cos(self.angle)*80),(py + math.sin(self.angle)*80))
        deg = -math.degrees(self.angle)
        if (deg < -90 or deg > 90) and not self.flipped:
            self.original_image = pygame.transform.flip(self.original_image, False, True)
            self.flipped = True
        elif (-90 <= deg <= 90) and self.flipped:
            self.original_image = pygame.transform.flip(self.original_image, False, True)
            self.flipped = False

        #print(deg)
        #print(self.flipped)

        self.image = pygame.transform.rotate(self.original_image, deg)
        self.rect = self.image.get_rect(center = pos)
        screen.blit(self.image, [self.rect.left - player.sprite.rect.centerx + SCREENSIZE[0] / 2,
                                 self.rect.top - player.sprite.rect.centery + SCREENSIZE[1] / 2])


class Blocks(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,color):
        super().__init__()
        self.image = pygame.Surface((w,h))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (x , y)
    
    def update(self):
        screen.blit(self.image, [self.rect.left - player.sprite.rect.centerx + SCREENSIZE[0] / 2,
                                 self.rect.top - player.sprite.rect.centery + SCREENSIZE[1] / 2])
        
player.add(Player(500,0,50,50,BLUE))
gun.add(Gun(10,10))
blocks.add(Blocks(400,700,1000,100,GREEN))
blocks.add(Blocks(100,100,200,500,GREEN))


# for y,i in enumerate(level):
#    for x,j in enumerate(i):
 #       if j == "X":
 #           blocks.add(Blocks(x*64,y*64,64,64,GREEN))
        # if j == "P":
        #     player.add(Player(x*64,y*64,50,50,BLUE))


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit() 

        if event.type == pygame.MOUSEBUTTONDOWN:
                gun.sprite.shoot()

        if event.type == pygame.VIDEORESIZE:
            SCREENSIZE = [event.w, event.h]

            screen = pygame.display.set_mode(SCREENSIZE, flags=pygame.RESIZABLE, vsync=1)

    screen.fill(AQUA)
    blocks.update()
    player.update()
    px, py = player.sprite.rect.center
    cx, cy = px - SCREENSIZE[0], py - SCREENSIZE[1]
    #print(px, py, cx, cy)
    gun.update(px,py)
        
    
    
    pygame.display.flip()  
    
    clock.tick(FPS)
