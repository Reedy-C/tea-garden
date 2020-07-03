from garden import Garden
import garden
from dgeann import dgeann
import garden_task as gt
import tako
from widget import *
import time
import os, sys
import pygame
from pygame.locals import *
import csv
from collections import deque
import tako_genetics as tg

class garden_game:
    def __init__(self, garden_size, tako_number, pop_max, max_width, max_height,
                 display_off, learning_on, genetic_mode, rand_nets, garden_mode,
                 filename, export_all, family_mod, family_detection, seed=None):
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
        task = gt.garden_task(env, learning_on)
        self.filename = filename
        self.export_all = export_all

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
        if collect_data or self.export_all:
            dead_tako = deque()
        while 1:
            #see if ending conditions have been met
            if max_ticks > 0:
                if self.stepid > max_ticks:
                    if collect_data or self.export_all:
                        for tako in env.tako_list:
                            dead_tako.append([tako, self.stepid])
                        if self.export_all:
                            export(dead_tako, self.filename)
                        if collect_data:
                            write_csv(self.filename, i, dead_tako)
                    return
            if max_gen > 0:
                if env.highest_gen > max_gen:
                    if collect_data or self.export_all:
                        for tako in env.tako_list:
                            dead_tako.append([tako, self.stepid])
                        if self.export_all:
                            export(dead_tako, self.filename)
                        if collect_data:
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
                if self.export_all:
                    export(dead_tako, self.filename)
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
                    if collect_data or self.export_all:
                        dead_tako.append([tako, self.stepid])
                    tako.kill()
            #check for data collection
            if self.stepid % 3000 == 0:
                if self.export_all:
                    export(dead_tako, self.filename)
                if collect_data:
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
        for sprite in env.new_sprites:
            if not isinstance(sprite, Dirt):
                if not isinstance(sprite, tako.Tako):
                    self.widget_sprites.add(sprite)
                else:
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
                tako = l[0]
                healthchr_a = []
                healthchr_b = []
                if type(tako.genome) == tg.health_genome:
                    for a in tako.genome.healthchr_a:
                        healthchr_a.append(a.ident)
                    for b in tako.genome.healthchr_b:
                        healthchr_b.append(b.ident)
                if type(tako.parents[0]) != str:
                    writ.writerow([i, tako.ident, tako.parents[0].ident,
                                   tako.parents[1].ident, tako.age, tako.gen,
                                   len(tako.children), tako.mating_attempts,
                                   tako.accum_pain, tako.cod, l[1],
                                   tako.genome.mut_record, tako.parent_degree,
                                   tako.parent_genoverlap,
                                   tako.genome.disorder_count,
                                   healthchr_a, healthchr_b])
                else:
                    writ.writerow([i, tako.ident, tako.parents[0], tako.parents[1],
                                   tako.age, tako.gen,
                                   len(tako.children), tako.mating_attempts,
                                   tako.accum_pain, tako.cod, l[1],
                                   tako.genome.mut_record, tako.parent_degree,
                                   tako.parent_genoverlap,
                                   tako.genome.disorder_count,
                                   healthchr_a, healthchr_b])
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
        tak = tak[0]
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
def run_experiment(x_loops=15, max_ticks=0, display_off=True, garden_size=8,
                   tako_number=1, pop_max=30, max_width=1800, max_height=900,
                   collect_data=True, export_all=False, rand_nets=False,
                   max_gen = 505, genetic_mode="Plain", learning_on=False,
                   seeds=None, garden_mode="Diverse Static",
                   family_detection=None, family_mod=0, record_inbreeding=True,
                   inbreed_lim = 1.1, hla_genes=0, binary_health=0,
                   carrier_percentage=40, filename=""):
    if max_width % 50 != 0:
        max_width = max_width - (max_width % 50)
    if max_height % 50 != 0:
        max_height = max_height - (max_height % 50)

    
    #create csv files
    if collect_data or export_all:
        if filename == "":
            filename = str(int(time.time())) + ".csv"
        elif len(filename) < 4:
            filename = filename + ".csv"
        elif filename[-4:] != ".csv":
            filename = filename + ".csv"

        if not os.path.exists("Data"):
            os.makedirs("Data")

        i = 0
        if collect_data:
            if not os.path.exists(os.path.join("Data", filename)):
                with open(os.path.join("Data", filename), 'a', newline='') as\
                     csvfile:
                    writ = csv.writer(csvfile)
                    writ.writerow(['iteration', 'ID', 'parent1', 'parent2',
                                   'age', 'generation', '# children',
                                   'mating attempts', 'accum pain',
                                   'cause of death', 'timestep', 'mutations',
                                   'parent_degree', 'parent_genoverlap',
                                   '# disorders',
                                   'health a', 'health b'])
            else:
                with open(os.path.join("Data", filename), newline='') as\
                      csvfile:
                    reader = csv.DictReader(csvfile)
                    row = None
                    for row in reader: pass
                    if row != None:
                        i = int(row["iteration"]) + 1

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
    gt.family_detection = family_detection
    tako.record_inbreeding = record_inbreeding
    tako.inbreed_lim = inbreed_lim
    tako.hla_genes = hla_genes
    tako.binary_health = binary_health
    tako.carrier_percentage = carrier_percentage
    
    loop_limit = x_loops
    if loop_limit < 1:
        loop_limit = 1
    
    while loop_limit > 0:
        if seeds != None:
            #check if seeds is long enough
            if len(seeds) < loop_limit + i:
                for i in range(loop_limit + i - len(seeds)):
                    seeds.append(seeds[i])
            tako.set_seed(seeds[i])
            g = garden_game(garden_size, tako_number, pop_max, max_width,
                            max_height, display_off, learning_on, genetic_mode,
                            rand_nets, garden_mode, filename,
                            export_all, family_mod, family_detection,
                            seeds[i])
        else:
            g = garden_game(garden_size, tako_number, pop_max, max_width,
                            max_height, display_off, learning_on, genetic_mode,
                            rand_nets, garden_mode, filename, export_all,
                            family_mod, family_detection)
        if not display_off:
            main_window = g
            main_window.main_loop(max_ticks, max_gen, display_off,
                                  collect_data, garden_mode, i)
        else:
            g.main_loop(max_ticks, max_gen, display_off, collect_data,
                        garden_mode, i)
        loop_limit -= 1
        i += 1

#runs a garden experiment from a file
def run_from_file(f):
    #set defaults
    x_loops=1;max_ticks=0;display_off=True;garden_size=13;tako_number=20
    pop_max=40;max_width=1800;max_height=900;collect_data=True;export_all=False
    rand_nets=False;max_gen=2;genetic_mode="Plain";learning_on=False
    seeds=None;garden_mode="Diverse Static";family_detection=None;family_mod=0
    record_inbreeding=True;inbreed_lim=1.1;filename="default file"
    hla_genes=0;binary_health=0;carrier_percentage=40

    
    atr_dict = {"x_loops": x_loops, "max_ticks": max_ticks,
                "display_off": display_off, "garden_size": garden_size,
                "tako_number": tako_number, "pop_max": pop_max,
                "max_width": max_width, "max_height": max_height,
                "collect_data": collect_data, "export_all": export_all,
                "rand_nets": rand_nets, "max_gen": max_gen,
                "genetic_mode": genetic_mode, "learning_on": learning_on,
                "seeds": seeds, "garden_mode": garden_mode,
                "family_detection": family_detection, "family_mod": family_mod,
                "record_inbreeding": record_inbreeding,
                "inbreed_lim": inbreed_lim, "filename": filename,
                "hla_genes": hla_genes, "binary_health": binary_health,
                "carrier_percentage": carrier_percentage}
    
    ints = ["x_loops", "max_ticks", "garden_size", "tako_number", "pop_max",
            "max_width", "max_height", "max_gen", "hla_genes",
            "binary_health", "carrier_percentage"]
    floats = ["family_mod", "inbreed_lim"]
    strs = ["genetic_mode", "garden_mode", "filename"]
    bools = ["display_off", "collect_data", "export_all", "rand_nets",
             "learning_on", "record_inbreeding"]
    
    with open(f) as exp_file:
        for line in exp_file:
            #comments
            if line[0] == "#":
                pass
            #blank line = run what we have, then continue
            #to read the file for a new set of parameters
            elif line == "\n":
                run_experiment(atr_dict["x_loops"], atr_dict["max_ticks"],
                               atr_dict["display_off"], atr_dict["garden_size"],
                               atr_dict["tako_number"], atr_dict["pop_max"],
                               atr_dict["max_width"], atr_dict["max_height"],
                               atr_dict["collect_data"], atr_dict["export_all"],
                               atr_dict["rand_nets"], atr_dict["max_gen"],
                               atr_dict["genetic_mode"],
                               atr_dict["learning_on"],
                               atr_dict["seeds"], atr_dict["garden_mode"],
                               atr_dict["family_detection"],
                               atr_dict["family_mod"],
                               atr_dict["record_inbreeding"],
                               atr_dict["inbreed_lim"],
                               atr_dict["hla_genes"], atr_dict["binary_health"],
                               atr_dict["carrier_percentage"],
                               atr_dict["filename"])
                #reset defaults
                atr_dict = {"x_loops": x_loops, "max_ticks": max_ticks,
                    "display_off": display_off, "garden_size": garden_size,
                    "tako_number": tako_number, "pop_max": pop_max,
                    "max_width": max_width, "max_height": max_height,
                    "collect_data": collect_data, "export_all": export_all,
                    "rand_nets": rand_nets, "max_gen": max_gen,
                    "genetic_mode": genetic_mode, "learning_on": learning_on,
                    "seeds": seeds, "garden_mode": garden_mode,
                    "family_detection": family_detection, "family_mod": family_mod,
                    "record_inbreeding": record_inbreeding,
                    "inbreed_lim": inbreed_lim, "filename": filename,
                    "hla_genes": hla_genes, "binary_health": binary_health,
                    "carrier_percentage": carrier_percentage}
            else:
                #get rid of newline character
                line = line[:-1]
                line = line.split(": ")
                if line[0] in ints:
                    val = int(line[1])
                elif line[0] in floats:
                    val = float(line[1])
                elif line[0] in bools:
                    val = True if line[1] == "True" else False
                elif line[0] in strs:
                    val = line[1]
                elif line[0] == "family_detection":
                    if line[1] == "None":
                        val = None
                    else:
                        val = line[1]
                elif line[0] == "seeds":
                    val = line[1].split(" ")
                atr_dict[line[0]] = val
    #run the last one in the file
    run_experiment(atr_dict["x_loops"], atr_dict["max_ticks"],
                   atr_dict["display_off"], atr_dict["garden_size"],
                   atr_dict["tako_number"], atr_dict["pop_max"],
                   atr_dict["max_width"], atr_dict["max_height"],
                   atr_dict["collect_data"], atr_dict["export_all"],
                   atr_dict["rand_nets"], atr_dict["max_gen"],
                   atr_dict["genetic_mode"],
                   atr_dict["learning_on"],
                   atr_dict["seeds"], atr_dict["garden_mode"],
                   atr_dict["family_detection"],
                   atr_dict["family_mod"],
                   atr_dict["record_inbreeding"],
                   atr_dict["inbreed_lim"], atr_dict["hla_genes"],
                   atr_dict["binary_health"], atr_dict["carrier_percentage"],
                   atr_dict["filename"])
    
       
if __name__ == "__main__":
    run_from_file('run params example.txt')
