import math

import neat.nn.feed_forward
import neat.population
import pygame
import neat
import os
import time
import random
import pickle
pygame.font.init()
pygame.init()

SCREENN_WIDTH = 500
SCREEN_HEIGHT = 800

GEN = 0
HIGHSCORE = 0
DEAD = False

BIRD_IMAGES = [pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird2.png")))]
PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "pipe.png")))
BASE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "base.png")))
BG_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bg.png")))

SOUND_JUMP = pygame.mixer.Sound(os.path.join("sounds", "jump.mp3"))
SOUND_SCORE = pygame.mixer.Sound(os.path.join("sounds", "score.mp3"))
SOUND_DIE = pygame.mixer.Sound(os.path.join("sounds", "die.mp3"))
SOUND_DEAD = pygame.mixer.Sound(os.path.join("sounds", "dead.mp3"))
SOUND_TRACK = pygame.mixer.Sound(os.path.join("sounds", "track.mp3"))

STAT_FONT = pygame.font.SysFont("comicsans", 20)

TRAINING = True
GEN_NR = 420
MUTE = True
FAST = False

class Bird:
    IMAGES = BIRD_IMAGES
    MAX_ROTATION = 25
    ROTATION_VELOCITY = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0  #Ticks passed since last jump
        self.velocity = 0
        self.height = self.y
        self.image_count = 0
        self.image = self.IMAGES[0]
        self.moon = False

    def jump(self):
        if self.moon:
            self.velocity = -1
        else:
            self.velocity = -10.5

        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        if self.moon:
            #displacement = (self.velocity*self.tick_count + 1.5*self.tick_count**2)*0.05 #generelle bewegungsgeschwindigkeit jump/drop
            #displacement =(self.velocity*self.tick_count+2.962*self.tick_count**2-14.149*self.tick_count)*0.05
            displacement = self.velocity*self.tick_count+(1/20)*self.tick_count**2
        else:
            displacement = self.velocity*self.tick_count + 1.5*self.tick_count**2 #calculaates movement of bird frame per frame based on the previous jumps



        # If we are moving upwards, move a little bit more (can be messed with)
        if displacement < 0:
            if not self.moon:
                displacement -= 2
            else:
                displacement -= 2*0.05

        if self.moon:
            if displacement >= 5:
                displacement = 5
        else:
            if displacement >= 16:
                displacement = 16

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:  #tilting the bird as soon as it crosses the hight of its pre jump position
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:

            if self.tilt > -90:
                if self.moon:
                    self.tilt -= self.ROTATION_VELOCITY/5  #Nosediving when falling
                else:
                    self.tilt -= self.ROTATION_VELOCITY  #Nosediving when falling
    
    def draw(self, screen):
        self.image_count += 1

        if self.image_count < self.ANIMATION_TIME:
            self.image = self.IMAGES[0]
        elif self.image_count < self.ANIMATION_TIME*2:
            self.image = self.IMAGES[1]
        elif self.image_count < self.ANIMATION_TIME*3:
            self.image = self.IMAGES[2]
        elif self.image_count < self.ANIMATION_TIME*4:
            self.image = self.IMAGES[1]
        elif self.image_count == self.ANIMATION_TIME*4 + 1:
            self.image = self.IMAGES[0]
            self.image_count = 0

        if self.tilt <= -80:
            self.image = self.IMAGES[1]
            self.image_count = self.ANIMATION_TIME*2

        rotated_image = pygame.transform.rotate(self.image, self.tilt)
        new_rect = rotated_image.get_rect(center=self.image.get_rect(topleft = (self.x, self.y)).center)
        screen.blit(rotated_image, new_rect.topleft)

    def get_mask(self): # For pixel perfect collitions
        return pygame.mask.from_surface(self.image)


class Pipe:
    GAP = 200
    if FAST:
        VELOCITY = 13
    else:
        VELOCITY = 5
    HEIGHT = 0

    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bot = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMAGE, False, True)
        self.PIPE_BOT = PIPE_IMAGE

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bot = self.height + self.GAP

    def move(self):
        self.x -= self.VELOCITY

    def draw(self, screen):
        screen.blit(self.PIPE_TOP, (self.x, self.top))
        screen.blit(self.PIPE_BOT, (self.x, self.bot))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bot_mask = pygame.mask.from_surface(self.PIPE_BOT)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bot_offset = (self.x - bird.x, self.bot - round(bird.y))

        b_point = bird_mask.overlap(bot_mask, bot_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        
        return False


class Base:
    if FAST:
        VELOCITY = 13
    else:
        VELOCITY = 5
    WIDTH = BASE_IMAGE.get_width()
    IMAGE = BASE_IMAGE

    def __init__(self, y):
        self.y = y
        self.x1 = 0 
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH 

    def draw(self, screen):
        screen.blit(self.IMAGE, (self.x1, self.y))
        screen.blit(self.IMAGE, (self.x2, self.y))


def draw_screen(screen, birds, pipes, base, score, gen, highscroe, p_vel, bird_count, p_height, DEAD, velocity):
    screen.blit(BG_IMAGE, (0, 0))
    for pipe in pipes:
        pipe.draw(screen)
    if TRAINING:
        text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
        screen.blit(text, (10, 50))

        text = STAT_FONT.render("Gen: " + str(gen-1) + "/" + str(GEN_NR), 1, (255,255,255))
        screen.blit(text, (10, 10))

        text = STAT_FONT.render("H_score: " + str(highscroe), 1, (255,255,255))
        screen.blit(text, (10, 30))

        text = STAT_FONT.render("P_vel: " + str(p_vel), 1, (255,255,255))
        screen.blit(text, (10, 70))

        text = STAT_FONT.render("P_height: " + str(p_height), 1, (255,255,255))
        screen.blit(text, (10, 90))

        text = STAT_FONT.render("brds: " + str(bird_count), 1, (255,255,255))
        screen.blit(text, (10, 110))

        text = STAT_FONT.render("vel: " + str(velocity), 1, (255,255,255))
        screen.blit(text, (10, 130))

    else:
        text = pygame.font.SysFont("comicsans", 80).render(str(score), 1, (255,255,255))
        screen.blit(text, (220, 50))
        
        if DEAD:
            text = pygame.font.SysFont("comicsans", 80).render("YOU DIED", 1, (255,0,0))
            screen.blit(text, (50, 200))

    base.draw(screen)
    for bird in birds:
        bird.draw(screen)
    pygame.display.update()


def main(genomes, config):
    global GEN 
    global HIGHSCORE
    
    GEN += 1
    nets = []
    ge = []
    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(100, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(500)]
    screen = pygame.display.set_mode((SCREENN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    score = 0
    run = True
    while run:
        if FAST:
            clock.tick(60)
        else:
            clock.tick(30) # Tickrate
        bird_count = len(birds)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
        
        pipe_ind = 0
        if len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_ind = 1

        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe.ind = 1
        else:
            if FAST:
                Pipe.VELOCITY = 13
                Base.VELOCITY = 13
            else:
                Pipe.VELOCITY = 5
                Base.VELOCITY = 5    
            run = False
            break
        
        Pipe.HEIGHT = pipes[pipe_ind].height

        for x, bird in enumerate(birds):
            bird.move()
            if bird.y < pipes[pipe_ind].bot or bird.y > pipes[pipe_ind].height:
                ge[x].fitness += 0.1
            
            output = nets[x].activate((bird.y, abs(pipes[pipe_ind].height), abs(pipes[pipe_ind].bot)))

            if output[0] > 0.5: # if output-neuron is > 0.5 jummp else not jump
                bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 3
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            #if pipe.passed:
                #add_pipe = True
                #rem.append(pipe)     
            
            pipe.move()
        
        """if FAST:
            if score > 30:
                Pipe.VELOCITY = 25
                Base.VELOCITY = 25
            elif score > 25:
                Pipe.VELOCITY = 23
                Base.VELOCITY = 23
            elif score > 20:
                Pipe.VELOCITY = 21
                Base.VELOCITY = 21
            elif score > 15:
                Pipe.VELOCITY = 19
                Base.VELOCITY = 19
            elif score > 10:
                Pipe.VELOCITY = 17
                Base.VELOCITY = 17
            elif score > 5:
                Pipe.VELOCITY = 15
                Base.VELOCITY = 15
        else:
            if score > 20:
                Pipe.VELOCITY = 13
                Base.VELOCITY = 13
            elif score > 15:
                Pipe.VELOCITY = 11
                Base.VELOCITY = 11
            elif score > 10:
                Pipe.VELOCITY = 9
                Base.VELOCITY = 9
            elif score > 5:
                Pipe.VELOCITY = 7
                Base.VELOCITY = 7"""

        """if score<100:
            Pipe.VELOCITY= Base.VELOCITY = score*(2/15)+1
        else:
            Base.VELOCITY=Pipe.VELOCITY = 10"""

        Pipe.VELOCITY= Base.VELOCITY = 12.13 * math.log10(score + 9.37) -6.19;


        if add_pipe:
            score += 1

            if HIGHSCORE < score:
                HIGHSCORE = score

            for g in ge:
                if score < 10:
                    g.fitness += 3
                elif score < 20:
                    g.fitness += 4
                elif score < 25:
                    g.fitness += 5
                elif score < 30:
                    g.fitness += 6
                elif score < 35:
                    g.fitness += 7
                
            pipes.append(Pipe(500))         

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.image.get_height() >= 730 or bird.y < 0:
                ge[x].fitness -= 10 # Collision mit top oder bottom screen
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        if score == 1001:
            break

        base.move()
        draw_screen(screen, birds, pipes, base, score, GEN, HIGHSCORE, Pipe.VELOCITY, bird_count, Pipe.HEIGHT, DEAD, Pipe.VELOCITY)

def test_best_genome(config_path, genome_path='w_02.pkl'):
    DEAD = False
    # Laden der NEAT Konfiguration
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    # Laden des Gewinner-Genoms
    with open(genome_path, 'rb') as f:
        genome = pickle.load(f)

    # Erstellen des Netzwerkes aus dem Gewinner-Genom
    net = neat.nn.FeedForwardNetwork.create(genome, config)

    # Erstellen eines einzelnen Vogels statt einer ganzen Population
    bird = Bird(100, 350)
    base = Base(730)
    pipes = [Pipe(500)]
    screen = pygame.display.set_mode((SCREENN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    tick_count = 0
    mem = []
    if not MUTE:
        SOUND_TRACK.play(10)

    score = 0
    run = True
    while run:
        if FAST:
            clock.tick(60)
        else:
            clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        tick_count += 1

        # Hier die gleiche Logik zum Wählen der richtigen Pipe verwenden wie in main
        pipe_ind = 0
        if len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_ind = 1

        # Entscheidung des Netzwerks basierend auf der Position des Vogels und der nächsten Röhre
        output = net.activate((bird.y, abs(pipes[pipe_ind].height), abs(pipes[pipe_ind].bot)))

        if output[0] > 0.5:
            bird.jump()
            if not MUTE:
                sound_mem = int(tick_count / 10)
                if sound_mem not in mem:
                    mem.append(sound_mem)
                    SOUND_JUMP.play()

        bird.move()
        base.move()

        add_pipe = False
        rem = []
        for pipe in pipes:
            if pipe.collide(bird):
                if not MUTE:
                    SOUND_TRACK.stop()
                    SOUND_DIE.play()
                    SOUND_DEAD.play()
                DEAD = True
                print(score)
                run = False
                break
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        if FAST:
            if score > 50:
                Pipe.VELOCITY = 25
                Base.VELOCITY = 25
            elif score > 45:
                Pipe.VELOCITY = 23
                Base.VELOCITY = 23
            elif score > 40:
                Pipe.VELOCITY = 21
                Base.VELOCITY = 21
            elif score > 35:
                Pipe.VELOCITY = 19
                Base.VELOCITY = 19
            elif score > 30:
                Pipe.VELOCITY = 17
                Base.VELOCITY = 17
            elif score > 25:
                Pipe.VELOCITY = 15
                Base.VELOCITY = 15
        if score > 20:
            Pipe.VELOCITY = 13
            Base.VELOCITY = 13
        elif score > 15:
            Pipe.VELOCITY = 11
            Base.VELOCITY = 11
        elif score > 10:
            Pipe.VELOCITY = 9
            Base.VELOCITY = 9
        elif score > 5:
            Pipe.VELOCITY = 7
            Base.VELOCITY = 7

        

        if add_pipe:
            score += 1
            if not MUTE:
                SOUND_SCORE.play()
            pipes.append(Pipe(500))

        for r in rem:
            pipes.remove(r)

        if bird.y + bird.image.get_height() >= 730 or bird.y < 0:
            if not MUTE:
                SOUND_TRACK.stop()
                SOUND_DIE.play()
                SOUND_DEAD.play()
            DEAD = True
            print(score)
            break

        draw_screen(screen, [bird], pipes, base, score, 1, HIGHSCORE, Pipe.VELOCITY, 1, Pipe.HEIGHT, DEAD)
        if DEAD:
            time.sleep(7)
            break

def run(config_path, gen_nr):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    population = neat.Population(config)

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    winner = population.run(main, gen_nr) # Anzahl Generationen
    with open('w_02.pkl', 'wb') as output:
        pickle.dump(winner, output, 1)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config.txt")

    if TRAINING:
        run(config_path, GEN_NR)
    else:
        test_best_genome(config_path)