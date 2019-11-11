from garden import Garden
import garden
from dgeann import dgeann
from garden_task import garden_task
import tako
from widget import *
import time
import os, sys
import pygame
from pygame.locals import *
import csv
from collections import deque

class garden_game:
    def __init__(self, rand_chance, garden_size, tako_number, pop_max,
                 max_width, max_height, display_off, learning_on, genetic_mode,
                 rand_nets, garden_mode, filename, export_all, family_mod,
                 family_detection, seed=None):
        pygame.init()
        global scroll
        if not display_off:
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
            self.background = pygame.Surface(self.screen.get_size()).convert()
        else:
            scroll = False
        
        self.clock = pygame.time.Clock()

        global env
        env = Garden(garden_size, tako_number, pop_max, genetic_mode, rand_nets,
                     seed, display_off, garden_mode)
            
        global task
        task = garden_task(env, rand_chance, learning_on)
        self.filename = filename
        self.export_all = export_all
        if self.export_all:
            export(env.tako_list, filename)

        self.selected_Tako = None
        self.neur = None
        self.selected_Neuron = None

        self.stepid = 0

    def main_loop(self, max_ticks, max_gen, display_off, collect_data,
                  garden_mode, i):
        if not display_off:
            self.make_background()
        self.load_sprites()
        if not display_off:
            pygame.display.flip()
            self.cam = [0,0]
            font = pygame.font.Font(None, 18)
        if collect_data:
            dead_tako = deque()
        while 1:
            #see if ending conditions have been met
            if max_ticks > 0:
                if self.stepid > max_ticks:
                    if collect_data:
                        for tako in env.tako_list:
                            dead_tako.append([tako, self.stepid])
                        write_csv(self.filename, i, dead_tako)
                    return
            if max_gen > 0:
                if env.highest_gen > max_gen:
                    if collect_data:
                        for tako in env.tako_list:
                            dead_tako.append([tako, self.stepid])
                        write_csv(self.filename, i, dead_tako)
                    return
            if not display_off:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        return
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
                if collect_data:
                    if len(dead_tako) > 0:
                        write_csv(self.filename, i, dead_tako)
                print("Tako are dead :(")
                return
            #let experiment go a step
            task.interact_and_learn()
            if garden_mode == "Changing":
                if self.stepid > 0 and self.stepid % 100000 == 0:
                    env.switch_grasses()
            elif garden_mode == "Nutrition":
                if self.stepid > 0 and self.stepid % 40000 == 0:
                    env.switch_nutrition()
            # see if any are dead
            for tako in env.tako_list:
                if tako.dead == True:
                    env.garden_map[tako.y][tako.x] = Dirt(display_off,
                                                          tako.x, tako.y)
                    env.tako_list.remove(tako)
                    if collect_data:
                        dead_tako.append([tako, self.stepid])
                    tako.kill()
            #check for data collection
            if collect_data:
                if self.stepid % 3000 == 0:
                    write_csv(self.filename, i, dead_tako)
            #now, update sprites, then draw them if using graphics
            if env.new_sprites != []:
                self.get_new()
            self.widget_sprites.update()
            for tako in env.tako_list:
                tako.update()
            if not display_off:
                self.graphics_loop(scroll, font)
            self.stepid += 1
            
    
    def load_sprites(self):
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
        if self.export_all:
            ex = []
        for sprite in env.new_sprites:
            if not isinstance(sprite, Dirt):
                if not isinstance(sprite, tako.Tako):
                    self.widget_sprites.add(sprite)
                else:
                    if self.export_all:
                        ex.append(sprite)
                self.all_sprites.add(sprite)
            env.new_sprites.remove(sprite)
        if self.export_all:
            export(ex, self.filename)

    def draw_onscreen(self):
        for spr in self.all_sprites:
            if spr.x >= self.cam[0] and spr.x <= (self.cam[0] + spr_width):
                if spr.y >= self.cam[1] and spr.y <= (self.cam[1] + spr_height):
                    self.screen.blit(spr.image, spr.rect)

    def make_background(self):
        for x in range(env.size):
            for y in range(env.size):
                img, rect = load_image("dirt.png")
                self.background.blit(img, (x*50, y*50))
                
    def graphics_loop(self, scroll, font):
        self.screen.blit(self.background, (0, 0))
        if not scroll:
            self.all_sprites.draw(self.screen)
        else:
            self.draw_onscreen()
        #oh, and display which step we're on
        if pygame.font:
            text = font.render(str(self.stepid), 1, (255, 255, 255))
            textpos = text.get_rect(centerx=
                                    (self.screen.get_width() * 0.5))
            self.screen.blit(text, textpos)
        pygame.display.flip()
        #cap at x fps
        self.clock.tick(10)

def load_image(name, colorkey=None):
    fullname = os.path.join('img', name)
    image = pygame.image.load(fullname)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

#records data about an agent to a csv file on the agent's death
def write_csv(filename, i, q):  
    with open(os.path.join("Data", filename), 'a', newline='') as csvfile:
            writ = csv.writer(csvfile)
            j = 0
            k = len(q)
            while j < k:
                l = q.popleft()
                #l = tako, stepid
                tako = l[0]
                if type(tako.parents[0]) != str:
                    writ.writerow([i, tako.ident, tako.parents[0].ident,
                                   tako.parents[1].ident, tako.age, tako.gen,
                                   len(tako.children), tako.mating_attempts,
                                   tako.cod, l[1], tako.genome.mut_record,
                                   tako.parent_degree, tako.parent_genoverlap])
                else:
                    writ.writerow([i, tako.ident, tako.parents[0], tako.parents[1],
                                   tako.age, tako.gen,
                                   len(tako.children), tako.mating_attempts,
                                   tako.cod, l[1], tako.genome.mut_record,
                                   tako.parent_degree, tako.parent_genoverlap])
                j += 1
            

#export the genome of a tako to a csv file
#will use the same filename as write_csv as a subfolder name at the moment
#depreciated function, not recommended for mass use
def export_old(tako, filename):
    #if not os.path.exists('Exported Genomes'):
    #    os.makedirs('Exported Genomes')
    path = "Exported Genomes"
    if filename != "":
        path = os.path.join(path, filename)
        path = path[:-4]
    if not os.path.exists(path):
        os.makedirs(path)
    w = tako.ident + "_weights.csv"
    lay = tako.ident + "_layers.csv"
    with open(os.path.join(path, w), "a", newline="") as file:
        writ = csv.writer(file)
        writ.writerow(['dom', 'can_mut', 'can_dup', 'mut_rate', 'ident',
                      'weight', 'in_node', 'out_node', 'in_layer', 'out_layer',
                       'chromosome'])
        for gen in tako.genome.weightchr_a:
            writ.writerow([gen.dom, gen.can_mut, gen.can_dup, gen.mut_rate,
                           gen.ident, gen.weight, gen.in_node, gen.out_node,
                           gen.in_layer, gen.out_layer, "a"])
        for gen in tako.genome.weightchr_b:
            writ.writerow([gen.dom, gen.can_mut, gen.can_dup, gen.mut_rate,
                           gen.ident, gen.weight, gen.in_node, gen.out_node,
                           gen.in_layer, gen.out_layer, "b"])
    with open(os.path.join(path, lay), "a", newline="") as file:
        writ = csv.writer(file)
        writ.writerow(['dom', 'can_mut', 'can_dup', 'mut_rate', 'ident',
                       'inputs', 'nodes', 'layer_type', 'chromosome'])
        for gen in tako.genome.layerchr_a:
            writ.writerow([gen.dom, gen.can_mut, gen.can_dup, gen.mut_rate,
                           gen.ident, gen.inputs, gen.nodes, gen.layer_type,
                           "a"])
        for gen in tako.genome.layerchr_a:
            writ.writerow([gen.dom, gen.can_mut, gen.can_dup, gen.mut_rate,
                           gen.ident, gen.inputs, gen.nodes, gen.layer_type,
                           "b"])
            
#exports condensed version of weight genes to a single csv file in \Data
#one line for haploid agents, two for diploid
#each row contains the variable info for each of the agent's weight genes
#n.b. expects a standard genome to work properly
def export(tako_list, filename):
    for tak in tako_list:
        l1 = [tak.ident, "a"]
        for gen in tak.genome.weightchr_a:
            l1.append(gen.ident)
            l1.append(gen.weight)
            l1.append(gen.mut_rate)
            l1.append(gen.dom)
        f = os.path.join("Data", (filename[:-4] + " gene data.csv"))
        with open(f, 'a', newline="") as csvfile:
            writ = csv.writer(csvfile)
            writ.writerow(l1)
            if len(tak.genome.weightchr_b) != 0:
                l2 = [tak.ident, "b"]
                for gen in tak.genome.weightchr_b:
                    l2.append(gen.ident)
                    l2.append(gen.weight)
                    l2.append(gen.mut_rate)
                    l2.append(gen.dom)   
                writ.writerow(l2)

#helper function for export, run from __init__
#makes the headers for the gene export CSV file
def make_headers():
    headers = ["agent_ident", "chro"]
    for i in range(10):
        for j in range(5):
            s = "d" + str(i) + "e" + str(j)
            headers.append(s + "_gene ident")
            headers.append(s + "_weight")
            headers.append(s + "_mut")
            headers.append(s + "_dom")
    for j in range(5):
        s = "d" + "a" + "e" + str(j)
        headers.append(s + "_gene ident")
        headers.append(s + "_weight")
        headers.append(s + "_mut")
        headers.append(s + "_dom")
    for j in range(5):
        s = "d" + "b" + "e" + str(j)
        headers.append(s + "_gene ident")
        headers.append(s + "_weight")
        headers.append(s + "_mut")
        headers.append(s + "_dom")
    for i in range(6):
        for j in range(5):
            s = "s" + str(i) + "e" + str(j)
            headers.append(s + "_gene ident")
            headers.append(s + "_weight")
            headers.append(s + "_mut")
            headers.append(s + "_dom")
    for i in range(5):
        for j in range(6):
            s = "e" + str(i) + "a" + str(j)
            headers.append(s + "_gene ident")
            headers.append(s + "_weight")
            headers.append(s + "_mut")
            headers.append(s + "_dom")
    return headers
    
#x_loops (int): run x times (<1 interpreted as 1)
#max_ticks (int): limit to x ticks (<= 0 interpreted as 'until all dead')
#display_off (bool): if true, does not display anything; otherwise, runs
#                   a pygame display capped at 10FPS
#rand_chance (int): make 1/x actions randomly different
#                   (<=1 interpreted as no random)
#garden_size (int): garden size in length/width in tiles
#tako_number (int): number of creatures created in the garden at startup
#pop_max (int): the maximum population that will be allowed at any time
#max_width (int): max horizontal resolution of window
#max_height (int): max vertical resolution of window
#collect_data (bool): creates csv file with various data on agents
#export_all (bool): on creation, each agent's genome is exported to csv file
#rand_nets (bool): use random weights to start first generation
#                   rather than starting genomes ('plain' style, except for dom)
#max_gen (int): limit to x generations; stops when first x+1 is born
#               (<=0 interpreted as 'until all dead')
#genetic_mode (str): haploid, plain (two copies of same genome), diverse
#                   (two different copies); not used if rand_nets is on
#learning_on (bool): turns learning on/off
#seeds (list): if not none, random seeds are used when starting a loop
#garden_mode (str): one of four values: "Diverse Static" (two grass types),
#                   "Single Static" (one),
#                   "Nutrition" (nutritive value changes),
#                   "Changing" (grass type switches)
#family_detection (str): one of three values, allowing agents to detect
#                    genetic or familial relationships with other agents:
#                    Degree (finds degree separation of relatives)
#                    Genoverlap (how much do their weight genes overlap?)
#                    None (disables)
#family_mod (float): modulates the above kinship detection, values 0~1
#record_inbreeding (bool): if True, records genetic and familial relationship
#                          b/w parents of an agent
#inbred_lim (float): if set to b/w 0 and 1, will only allow agents to live if
#                    the genetic relationship b/w parents is < inbred_lim
def run_experiment(x_loops=15, max_ticks=0, display_off=True, rand_chance=0,
                   garden_size=8, tako_number=1, pop_max=30, max_width=1800,
                   max_height=900, collect_data=True, export_all=False,
                   rand_nets=False, max_gen = 505, genetic_mode="Plain",
                   learning_on=False, seeds=None, garden_mode="Diverse Static",
                   family_detection=None, family_mod=0, record_inbreeding=True,
                   inbreed_lim = 1.1):
    if max_width % 50 != 0:
        max_width = max_width - (max_width % 50)
    if max_height % 50 != 0:
        max_height = max_height - (max_height % 50)

    
    #create csv files
    if collect_data or export_all:
        filename = input("Filename for .csv files?")
        if filename == "":
            filename = str(int(time.time())) + ".csv"
        elif len(filename) < 4:
            filename = filename + ".csv"
        elif filename[-4:] != ".csv":
            filename = filename + ".csv"

        if not os.path.exists("Data"):
            os.makedirs("Data")
            
        if collect_data:
            if not os.path.exists(os.path.join("Data", filename)):
                with open(os.path.join("Data", filename), 'a', newline='') as\
                     csvfile:
                    writ = csv.writer(csvfile)
                    writ.writerow(['iteration', 'ID', 'parent1', 'parent2',
                                   'age', 'generation', '# children',
                                   'mating attempts', 'cause of death',
                                   'timestep', 'mutations', 'parent_degree',
                                   'parent_genoverlap'])
                i = 0
            else:
                with open(os.path.join("Data", filename), newline='') as\
                      csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader: pass
                    i = int(row["iteration"]) + 1
        else:
            i = 0

        if export_all:
            h = make_headers()
            f = os.path.join('Data', (filename[:-4] + ' gene data.csv'))
            if not os.path.exists(f):
                with open(f, 'a') as file:
                    writ = csv.writer(file)
                    writ.writerow(h)

    tako.rand_nets = rand_nets
    tako.family_mod = family_mod
    tako.family_detection = family_detection
    tako.record_inbreeding = record_inbreeding
    tako.inbreed_lim = inbreed_lim
    
    loop_limit = x_loops
    if loop_limit < 1:
        loop_limit = 1
    
    while loop_limit > 0:
        if seeds != None:
            #check if seeds is long enough
            if len(seeds) < loop_limit:
                for i in range(loop_limit - len(seeds)):
                    seeds.append(seeds[i])
            tako.set_seed(seeds[i])
            g = garden_game(rand_chance, garden_size, tako_number,
                            pop_max, max_width, max_height,
                            display_off, learning_on, genetic_mode,
                            rand_nets, garden_mode, filename,
                            export_all, family_mod, family_detection,
                            seeds[i])
        else:
            g = garden_game(rand_chance, garden_size, tako_number,
                                     pop_max, max_width, max_height,
                                     display_off, learning_on, genetic_mode,
                                     rand_nets, garden_mode, filename,
                                     export_all, family_mod, family_detection)
        if not display_off:
            main_window = g
            main_window.main_loop(max_ticks, max_gen, display_off,
                                  collect_data, garden_mode, i)
        else:
            g.main_loop(max_ticks, max_gen, display_off, collect_data,
                        garden_mode, i)
        loop_limit -= 1
        i += 1
       
if __name__ == "__main__":
    seeds = ["evo", "genome", "diploidy", "haploidy", "tako",
             "selection", "ika", "mate", "mutation", "network",
             "gene", "advantage", "children", "parents", "identity",
             "input", "output", "hidden", "weights", "crossover"]
    run_experiment(garden_size=13, tako_number=20, x_loops=1,
                   pop_max=40, max_gen=2, collect_data=True, seeds=seeds,
                   genetic_mode="Plain", garden_mode="Diverse Static") 
