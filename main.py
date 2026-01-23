import pygame,sys,math


pygame.font.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(40)
SCREENSIZE = [800,800]
FPS = 60
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




class Player(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,color):
        super().__init__()
        self.image = pygame.Surface((w,h))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = x,y
        
        self.centerx = x
        self.centery = y
        self.velx = 0
        self.vely = 0
     
     
    def add_vel(self,x,y):
        self.velx += x
        self.vely += y
     
        
    def physics(self):
        self.vely += 0.4
        
        if self.velx > 0:
            if self.velx <= 0.05:
                self.velx = 0
            
            else:
                self.velx -= 0.05
            
        if self.velx < 0:
            if self.velx >= 0.05:
                self.velx = 0
            
            else:
                self.velx += 0.05

        
        
        # if self.vely > 0:
        #     if self.vely <= 0.2:
        #         self.vely = 0
            
        #     else:
        #         self.vely -= 0.2
            
        # if self.vely < 0:
        #     if self.vely >= 0.2:
        #         self.vely = 0
            
        #     else:
        #         self.vely += 0.2
                
        
        
        
        
        
        
        
        
        
        self.rect.centerx += self.velx
        for sprite in pygame.sprite.spritecollide(self,blocks,False):
            if self.rect.colliderect(sprite.rect):
                if self.velx > 0:
                    self.rect.right = sprite.rect.left
                    self.velx = 0 
                elif self.velx < 0:
                    self.rect.left = sprite.rect.right
                    self.velx = 0 
        
        self.rect.centery += self.vely
        for sprite in pygame.sprite.spritecollide(self,blocks,False):
            if self.rect.colliderect(sprite.rect):
                if self.vely > 0:
                    self.rect.bottom = sprite.rect.top
                    self.vely = 0 
                elif self.vely < 0:
                    self.rect.top = sprite.rect.bottom
                    self.vely = 0 

        
        
  
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
        screen.blit(self.image,[self.rect.x,self.rect.y])
        gun.update(self.rect.centerx,self.rect.centery)
        
    
        
class Gun(pygame.sprite.Sprite):
    def __init__(self,w,h):
        super().__init__()
        self.image = pygame.Surface((w,h))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (10,10)
    
    def shoot(self):
        addvelx = -math.cos(self.angle)*18
        addvely = -math.sin(self.angle)*18
        player.sprite.add_vel(addvelx,addvely)
                
    
      
    def update(self,px,py):
        mx = pygame.mouse.get_pos()[0]
        my = pygame.mouse.get_pos()[1]
        self.angle = math.atan2(my-py,mx-px)
        print(f'x:{math.cos(self.angle)}, y:{math.sin(self.angle)}')
        self.rect.center = (px + math.cos(self.angle)*100,py + math.sin(self.angle)*100)
        
        
         
        
        
        screen.blit(self.image,[self.rect.x,self.rect.y])


class Blocks(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,color):
        super().__init__()
        self.image = pygame.Surface((w,h))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
    
    def update(self):
         screen.blit(self.image,[self.rect.x,self.rect.y])
        

player.add(Player(500,0,50,50,BLUE))
gun.add(Gun(10,10))
blocks.add(Blocks(400,700,1000,100,GREEN))
blocks.add(Blocks(100,100,200,500,GREEN))


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
            
    screen.fill(WHITE)
    player.update()
    blocks.update()
    

        
    
    
    pygame.display.flip()  
    
    clock.tick(FPS)
