import pygame
import time
import random
from copy import deepcopy
from NeuralNetwork import pynn

pygame.init()
pygame.font.init()

LOAD_FILE = "save.txt"
SAVE_FILE = "save2.txt"

CACTUS_HEIGHT = 100
CACTUS_WIDTH = 28
BIRD_BONUS = 50
WIDTH, HEIGHT = 1000, 400
GROUND_HEIGHT = 100
GRAVITY = 2684
JUMP_VELOCITY = -1000
SPEED = 1

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("dino game")
BG = pygame.transform.scale(pygame.image.load("grey.jpg"), (WIDTH, HEIGHT))


FONT = pygame.font.SysFont("arial", 30)
clock = pygame.time.Clock()

class obstacle:
    def __init__(self,type=None):
        types = ["bird","tall_cactus","short_cactus"]
        if type == None:
            self.type = random.randint(0,2)
        else:
            self.type = type
        self.typename = types[self.type]

        self.x = WIDTH
        if self.type == 0:
            self.width = 28
            self.height = 25
            self.level = random.randint(0,3)
            self.extra_vel = (self.level-2)*BIRD_BONUS
            extra = random.randint(25, 50)
            self.extra_vel = 0#(self.extra_vel+extra) if abs(self.extra_vel+extra) > abs(self.extra_vel) else (self.extra_vel-extra)
            self.y = HEIGHT - GROUND_HEIGHT - self.height*(1+self.level) - 10*(2*self.level+1)
        elif self.type == 1:
            self.height = 75
            self.width = 30*random.randint(1,3)
            self.y = HEIGHT - GROUND_HEIGHT - self.height
            self.extra_vel = 0
        elif self.type == 2:
            self.height = 125
            self.width = 32
            self.y = HEIGHT - GROUND_HEIGHT - self.height
            self.extra_vel = 0
    def create_obstacle(self):
        return pygame.Rect(self.x,self.y,self.width, self.height)


def draw(gen:pynn.generation, players, ground, elapsed_time, cacti):
    WIN.blit(BG, (0, 0)) 
    for color, player in zip(gen.colors, players):
        if player is None:
            continue
        pygame.draw.rect(WIN, color, player, width=3)

    pygame.draw.rect(WIN, (0,0,0), ground)
    for cactus in cacti:
        pygame.draw.rect(WIN, (255,0,0), cactus.create_obstacle())
    time_passed = str(round(elapsed_time*10))
    #if not (5-len(time_passed) < 0):
    #    time_text = FONT.render(f"BEST SCORE: {'0'*(max(0,5-len(time_passed))) + time_passed}", 1, "white")
    #else:
    #    time_text = FONT.render(f"BEST SCORE: {random.randint(10000,99999)}", 1, "white") 
    timmy = FONT.render(f"BEST SCORE: {-int(gen.get_best(get_loss=True))}", 1, "white") 
    WIN.blit(timmy, (10, 10))
    pygame.display.update()  

def main(gen:pynn.generation) :
    #Variables
    end = False
    PLAYER_HEIGHT = 60
    PLAYER_WIDTH = 40
    clock = pygame.time.Clock()
    
#===========================================================================
    while not end:
        player = pygame.Rect(100, HEIGHT - PLAYER_HEIGHT- GROUND_HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT)  
        ground = pygame.Rect(0, HEIGHT - GROUND_HEIGHT, WIDTH, GROUND_HEIGHT)  
        start_time = time.time()
        CACTUS_VEL = 300
        elapsed_time = 0    
        cactus_count = 0
        cactus_add_increment = 2000
        cacti = []
        randomizer = -2000
        run = True
        players = [deepcopy(player) for _ in range(gen.size)]
        for network in gen.networks:
                network.is_jumping = False
                network.velocity_y = 0
                network.loss = 0
                network.alive = True
        
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    gen.set_best_wb()
                    gen.save(SAVE_FILE)
                    pygame.quit()
                    end = True
                    exit()
            if all([player is None for player in players]):
                dead_text = FONT.render("HAHAHAHAHAHA YOU DIED LIKE HOW", 1, "white")
                WIN.blit(dead_text, (WIDTH/2 - dead_text.get_width()/2, HEIGHT/2 - dead_text.get_height()/2))
                pygame.display.update()
                run = False
                continue
            delta_time = clock.tick(60) / 1000.0 * SPEED
            cactus_count += delta_time * 1000
            CACTUS_VEL += delta_time * 10
            elapsed_time = time.time() - start_time
            
            if cactus_count > cactus_add_increment + randomizer:
                obst = obstacle()
                cacti.append(obst)
                cactus_add_increment = max(750, cactus_add_increment - 30)
                cactus_count = 0
                randomizer = random.randint(-200,0)
            ucacti = []
            cacti.sort(key=lambda cactus: cactus.x)
            for cactus in cacti:
                if not cactus.x + cactus.width < 100:
                    ucacti.append(cactus)
            
            for i in range(len(players[:])):
                player = players[i]
                NN = gen.networks[i]
                if player is None:
                    continue
                data = [player.y, NN.velocity_y]
                
                c = obstacle(type=0) if len(ucacti) == 0 else ucacti[0]
                data.extend([c.x - 100, c.height, c.width, c.type == 0, c.type == 1, c.type == 2])  # One-hot encoding

                c = obstacle(type=0) if len(ucacti) < 2 else ucacti[1]
                data.extend([c.x - 100, c.height, c.width, c.type == 0, c.type == 1, c.type == 2])  # One-hot encoding

                nn_output=NN.activate(data)
                if nn_output==1 and NN.is_jumping is False:
                    NN.velocity_y = JUMP_VELOCITY
                    NN.is_jumping = True
                    player.height = PLAYER_HEIGHT
                    player.width = PLAYER_WIDTH
                    player.y = HEIGHT - player.height - GROUND_HEIGHT 
                elif nn_output == 0:
                    
                    if NN.is_jumping:
                        NN.velocity_y = max(0,NN.velocity_y)
                        NN.velocity_y += 250
                        NN.loss -= 0.5
                    else:
                        player.height = 30
                        player.width = 50
                        player.y = HEIGHT - player.height - GROUND_HEIGHT
                        NN.loss -= 1
                    
                if NN.is_jumping:
                    NN.velocity_y += GRAVITY * delta_time
                    player.y += NN.velocity_y * delta_time 

                if player.y + PLAYER_HEIGHT >= HEIGHT - GROUND_HEIGHT: 
                    player.y = HEIGHT - player.height - GROUND_HEIGHT   
                    NN.is_jumping = False
                    NN.velocity_y = 0

            for cactus in cacti[:2]:
                cactus.x -= (CACTUS_VEL + cactus.extra_vel) * delta_time
                if cactus.x < -cactus.width:
                    cacti.remove(cactus)
                    continue
                for network, (i, player) in zip(gen.networks,enumerate(players[:])):              
                    if player is None:
                        continue
                    if player.x < cactus.x + cactus.width and player.x + player.width > cactus.x:
                        if cactus.create_obstacle().colliderect(player):
                            players[i] = None 
                            network.alive = False
                            if cactus.type != 0:
                                network.loss += 100
                        elif player.y < cactus.y:
                            network.loss -= 5 * cactus.type
            draw(gen, players, ground, elapsed_time, cacti)
        #print([layer.best_weights for layer in gen.networks[0].layers])
        #print([network.loss for network in gen.networks])
        gen.set_best_wb()
        gen.repopulate(gen.get_best())
        gen.mutate_gen(limit=1) 
#==========================================================================
if __name__ == "__main__":        
    #create Neural Network
    n_inputs = 14 # y; speed; [distance to cactus; cactus height; cactus width; height] *2;
    #NN = pynn.Neural_Network()
    #NN.create((14,8,8,1),[1,1,0])
    #gen = pynn.generation(NN,100)
    gen = pynn.load(LOAD_FILE)
    gen.mutate_gen(limit=1)
    #print(gen.networks[0].layers[0].weights)
    gen.colors = [(random.randint(100,255), random.randint(100,255), random.randint(100,255)) for _ in range(gen.size)] 
    pygame.init()
    pygame.font.init()
    WIN = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("dino game")
    BG = pygame.transform.scale(pygame.image.load("grey.jpg"), (WIDTH, HEIGHT))
    FONT = pygame.font.SysFont("arial", 30)
    clock = pygame.time.Clock()
    main(gen)
    
    #print([layer.best_weights for layer in gen.networks[0].layers])
    #print([network.loss for network in gen.networks])
    #print(gen.generation_lowest_loss)

