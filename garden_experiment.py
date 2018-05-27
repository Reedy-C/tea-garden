from garden import Garden
from garden_task import GardenTask
import tako
from widget import *
import time
import os, sys
import pygame
import math
from pygame.locals import *
import numpy
import caffe
sys.path.append('..')
from dgeann import dgeann
import csv



class garden_game:

    def __init__(self, rand_chance, garden_size, tako_number, pop_max,
                 max_width, max_height, learning_on, genetic_mode, rand_nets,
                 seed=None):
        pygame.init()

        global scroll
        scroll = True

        self.width = (garden_size * 50)
        self.height = (garden_size * 50)
        if self.width <= max_width and self.height <= max_height:
            self.screen = pygame.display.set_mode((self.width, self.height))
            scroll = False
        elif self.width > max_width and self.height <= max_height:
            self.screen = pygame.display.set_mode((max_width, self.height))
        elif self.width <= max_width and self.height > max_height:
            self.screen = pygame.display.set_mode((self.width, max_height))
        else:
            self.screen = pygame.display.set_mode((max_width, max_height))

        global spr_height
        spr_height = self.screen.get_size()[1] / 50
        global spr_width
        spr_width = self.screen.get_size()[0] / 50
        
        pygame.display.set_caption('Garden')
        self.clock = pygame.time.Clock()

        self.neur_background = pygame.Surface(self.screen.get_size()).convert()

        global env
        env = Garden(garden_size, tako_number, pop_max, genetic_mode, rand_nets,
                     seed)
        global task
        task = GardenTask(env, rand_chance, learning_on)

        self.selected_Tako = None
        self.neur = None
        self.selected_Neuron = None

        self.stepid = 0

    def MainLoop(self, max_steps, max_gen, speedup, collect_data, filename, i):
        self.load_sprites()
        pygame.display.flip()
        self.cam = [0,0]
        font = pygame.font.Font(None, 18)
        while 1:
            if max_steps > 0:
                if self.stepid > max_steps:
                    return
            #probably not the most elegant way to do this, but it works
            if max_gen > 0:
                if env.highest_gen > max_gen:
                    return
            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                elif event.type == MOUSEBUTTONDOWN:
                    # returns x,y with origin in upper left
                    x = event.pos[0]
                    y = event.pos[1]
                elif event.type == KEYDOWN:
                    if scroll:
                        if event.key == K_LEFT:
                            if self.cam[0] > 0:
                                self.cam[0] -= 1
                                for spr in self.all_sprites:
                                    spr.move_rect(1, 0)
                        elif event.key == K_RIGHT:
                            if self.cam[0] < env.size - spr_width:
                                self.cam[0] += 1
                                for spr in self.all_sprites:
                                    spr.move_rect(-1, 0)
                        elif event.key == K_UP:
                            if self.cam[1] > 0:
                                self.cam[1] -= 1
                                for spr in self.all_sprites:
                                    spr.move_rect(0, 1)
                        elif event.key == K_DOWN:
                            if self.cam[1] < env.size - spr_height:
                                self.cam[1] += 1
                                for spr in self.all_sprites:
                                    spr.move_rect(0, -1)
            #see if all are dead
            if len(env.tako_list) == 0:
                print("Tako are dead :(")
                return
            #let experiment go a step
            task.interact_and_learn()
            self.screen.blit(self.neur_background, (0, 0))
            # see if any are dead
            for tako in env.tako_list:
                if tako.dead == True:
                    env.garden_map[tako.y][tako.x] = Dirt(tako.x, tako.y)
                    env.tako_list.remove(tako)
                    if collect_data:
                        write_csv(filename, tako, i, self.stepid)
                    tako.kill()
            #now, update sprites, then draw them
            if env.new_sprites != []:
                self.get_new()
            self.widget_sprites.update()
            for tako in env.tako_list:
                tako.update()
            if not scroll:
                self.all_sprites.draw(self.screen)
            else:
                self.draw_onscreen()
            #oh, and display which step we're on
            if not speedup:
                if pygame.font:
                    text = font.render(str(self.stepid), 1, (255, 255, 255))
                    textpos = text.get_rect(centerx=
                                            (self.screen.get_width() * 0.5))
                    self.screen.blit(text, textpos)
            pygame.display.flip()
            #cap at x fps
            if not speedup:
                self.clock.tick(10)
            self.stepid += 1
            
    
    def load_sprites(self):
        self.make_background()
        self.widget_sprites = pygame.sprite.Group()
        for x in range(env.size):
            for y in range(env.size):
                if type(env.garden_map[y][x]) != tako.Tako:
                    if type(env.garden_map[y][x]) != Dirt:
                        self.widget_sprites.add(env.garden_map[y][x])
        env.new_sprites = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        for tak in env.tako_list:
            self.all_sprites.add(tak)
        for sprite in self.widget_sprites:
            self.all_sprites.add(sprite)

    def get_new(self):
        for sprite in env.new_sprites:
            if not isinstance(sprite, Dirt):
                if not isinstance(sprite, tako.Tako):
                    self.widget_sprites.add(sprite)
                self.all_sprites.add(sprite)
            env.new_sprites.remove(sprite)

    def draw_onscreen(self):
        for spr in self.all_sprites:
            if spr.x >= self.cam[0] and spr.x <= (self.cam[0] + spr_width):
                if spr.y >= self.cam[1] and spr.y <= (self.cam[1] + spr_height):
                    self.screen.blit(spr.image, spr.rect)

    def make_background(self):
        for x in range(env.size):
            for y in range(env.size):
                img, rect = load_image("dirt.png")
                self.neur_background.blit(img, (x*50, y*50))

def load_image(name, colorkey=None):
    fullname = os.path.join('img', name)
    image = pygame.image.load(fullname)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

#records data to a csv file on an agent's death
def write_csv(filename, tako, i, step):
    if not os.path.exists("Data"):
        os.makedirs("Data")
    if not os.path.exists(os.path.join("Data", filename)):
        with open(os.path.join("Data", filename), 'a', newline='') as csvfile:
            writ = csv.writer(csvfile)
            writ.writerow(['iteration', 'ID', 'parent1', 'parent2', 'age',
                           'generation', '# children',
                           'mating attempts', 'cause of death', 'timestep'])
    #write above data
    with open(os.path.join("Data", filename), 'a', newline='') as csvfile:
            writ = csv.writer(csvfile)
            writ.writerow([i, tako.ident, tako.parents[0], tako.parents[1],
                           tako.age, tako.gen, len(tako.children),
                           tako.mating_attempts, tako.cod, step])

#export the genome of a tako to a csv file
def export(tako):
    if not os.path.exists('Exported Genomes'):
        os.makedirs('Exported Genomes')
    fa = tako.ident + "_a"
    fb = tako.ident + "_b"
    with open(os.path.join("Exported Genomes", fa), "a", newline="") as file:
        writ = csv.writer(file)
        for gen in tako.genome.weightchr_a:
            writ.writerow([gen.dom, gen.can_mut, gen.can_dup, gen.mut_rate,
                           gen.ident, gen.weight, gen.in_node, gen.out_node,
                           gen.in_layer, gen.out_layer])
    with open(os.path.join("Exported Genomes", fb), "a", newline="") as file:
        writ = csv.writer(file)
        for gen in tako.genome.weightchr_b:
            writ.writerow([gen.dom, gen.can_mut, gen.can_dup, gen.mut_rate,
                           gen.ident, gen.weight, gen.in_node, gen.out_node,
                           gen.in_layer, gen.out_layer])
    
#x_loops (int): run x times (<1 interpreted as 1)
#max_steps (int): limit to x timesteps (<= 0 interpreted as 'until all dead')
#speedup (bool): run simulation quickly if true, slow to 10fps if false
#rand_chance (int): make 1/x actions randomly different
#                   (<=1 interpreted as no random)
#garden_size (int): garden size in length/width in tiles
#tako_number (int): number of creatures created in the garden
#pop_max (int): the maximum population that will be allowed at any time
#max_width (int): max horizontal resolution of window
#max_height (int): max vertical resolution of window
#collect_data (bool): creates csv file with various data on agents
#rand_nets (bool): use random weights to start first generation
#                   rather than starting genomes ('plain' style, except for dom)
#max_gen (int): limit to x generations; stops when first x+1 is born
#               (<=0 interpreted as 'until all dead')
#haploid_mode (bool): run with haploid rather than diploid genetics mode
#genetic_mode (str): haploid, plain (two copies of same genome), diverse
#                   (two different copies); not used if rand_nets is on
#learning_on (bool): turns learning on/off
#seeds (bool): uses the list of random starting seeds to set starting condition
def run_experiment(x_loops=15, max_steps=0, speedup=True, rand_chance=20,
                   garden_size=8, tako_number=1, pop_max=30, max_width=1800,
                   max_height=900, collect_data=True, rand_nets=False,
                   max_gen = 505, genetic_mode="Plain", learning_on=True,
                   seeds=False):
    if max_width % 50 != 0:
        max_width = max_width - (max_width % 50)
    if max_height % 50 != 0:
        max_height = max_height - (max_height % 50)


    filename = ""
    if collect_data:
        filename = input("Filename for csv?")
        if filename == "":
            filename = str(int(time.time())) + ".csv"
        elif len(filename) < 4:
            filename = filename + ".csv"
        elif filename[-3] != ".csv":
            filename = filename + ".csv"

    if rand_nets:
        tako.rand_nets = True
    
    loop_limit = x_loops
    if loop_limit < 1:
        loop_limit = 1
    i = 0

    seeds = ["evo", "genome", "diploidy", "haploidy", "tako",
             "selection", "ika", "mate", "mutation", "network",
             "gene", "advantage", "children", "parents", "identity",
             "input", "output", "hidden", "weights", "crossover"]
    
    while loop_limit > 0:
        if seeds == True:
            MainWindow = garden_game(rand_chance, garden_size, tako_number,
                                     pop_max, max_width, max_height,
                                     learning_on, genetic_mode, rand_nets,
                                     seeds[i])
        else:
            MainWindow = garden_game(rand_chance, garden_size, tako_number,
                                     pop_max, max_width, max_height,
                                     learning_on, genetic_mode, rand_nets)
        MainWindow.MainLoop(max_steps, max_gen, speedup, collect_data,
                            filename, i)
        loop_limit -= 1
        i += 1
                
if __name__ == "__main__":
    run_experiment(garden_size=13, tako_number=20, x_loops=5,
                   pop_max=40, max_gen = 100, learning_on=False)
