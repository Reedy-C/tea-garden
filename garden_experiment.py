from collections import deque
import csv
import os
import random
import time

import pygame
from pygame.locals import *
from garden import Garden
import garden_task as gt
import tako
import tako_genetics as tg
from widget import Dirt


class garden_game:
    def __init__(self, garden_size, tako_number, pop_max, max_width, max_height,
                 display_on, max_fps, learning_on, genetic_mode, rand_nets,
                 garden_mode, filename, export_all, family_mod,
                 family_detection,two_envs, diff_envs, migration_rate,
                 seed=None):
        pygame.init()

        if display_on:
            self.scroll = True
            self.max_fps = max_fps

            self.width = (garden_size * 50)
            self.height = (garden_size * 50)
            if self.width <= max_width and self.height <= max_height:
                self.screen = pygame.display.set_mode((self.width, self.height))
                self.scroll = False
            elif self.width > max_width and self.height <= max_height:
                self.screen = pygame.display.set_mode((max_width, self.height))
            elif self.width <= max_width and self.height > max_height:
                self.screen = pygame.display.set_mode((self.width, max_height))
            else:
                self.screen = pygame.display.set_mode((max_width, max_height))

            self.spr_height = self.screen.get_size()[1] / 50
            self.spr_width = self.screen.get_size()[0] / 50
        
            pygame.display.set_caption('Garden')
            self.background = pygame.Surface(self.screen.get_size()).convert()
        else:
            self.scroll = False
        
        self.clock = pygame.time.Clock()
        self.two_envs = two_envs
        self.diff_envs = diff_envs
        self.migration_rate = migration_rate

        if self.diff_envs:
            env0 = Garden(garden_size, tako_number, pop_max, genetic_mode,
                          rand_nets, seed, display_on, garden_mode, food=0)
        else:
            env0 = Garden(garden_size, tako_number, pop_max, genetic_mode,
                          rand_nets, seed, display_on, garden_mode)
        env0.env_id = 0
        self.env_list = [env0]

        #TODO
        #figure out if I need to/how to fix the seed issue
        #(which is that the same random seed is shared between the two
        #Garden environments, so actions in one advance the seed for
        #the other as well)
        if self.two_envs:
            if self.diff_envs:
                env1 = Garden(garden_size, tako_number, pop_max, genetic_mode,
                              rand_nets, seed, display_on, garden_mode, food=1)
            else:
                env1 = Garden(garden_size, tako_number, pop_max, genetic_mode,
                              rand_nets, seed, display_on, garden_mode)
            env1.env_id = 1
            self.env_list.append(env1)

        task0 = gt.garden_task(env0, learning_on)
        self.task_list = [task0]
        if self.two_envs:
            task1 = gt.garden_task(env1, learning_on)
            self.task_list.append(task1)
            
        self.filename = filename
        self.export_all = export_all
        self.stepid = 0
        self.current_env = 0

    def main_loop(self, max_steps, max_gen, display_on, collect_data,
                  garden_mode, i):
        if display_on:
            self.make_background()
        self.load_sprites()
        if display_on:
            pygame.display.flip()
            self.cam = [0,0]
            font = pygame.font.Font(None, 18)
        if collect_data or self.export_all:
            dead_tako = deque()
        while 1:
            #see if ending conditions have been met
            if max_steps > 0:
                if self.stepid > max_steps:
                    if collect_data or self.export_all:
                        for env in self.env_list:
                            for tak in env.tako_list:
                                dead_tako.append([tak, self.stepid,
                                                  env.env_id])
                            if self.export_all:
                                export(dead_tako, self.filename)
                            if collect_data:
                                write_csv(self.filename, i, dead_tako)
                    return
            end = False
            if max_gen > 0:
                for env in self.env_list:
                    if env.highest_gen > max_gen:
                        end = True
                        for en in self.env_list:
                            for tak in en.tako_list:
                                dead_tako.append([tak, self.stepid,
                                                  en.env_id])
            #if we have not met the predefined end conditions, begin main loop
            if display_on:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        return
                    elif event.type == KEYDOWN:
                        if self.two_envs:
                            if event.key == K_s:
                                if self.current_env == 0:
                                    self.current_env = 1
                                else:
                                    self.current_env = 0
                                self.load_sprites()
                        if self.scroll:
                            #TODO this is glitchy with two envs and switching
                            if event.key == K_LEFT:
                                if self.cam[0] > 0:
                                    self.cam[0] -= 1
                                    for spr in self.all_sprites:
                                        spr.move_rect(1, 0)
                            elif event.key == K_RIGHT:
                                if self.cam[0] < (self.env_list[0].size -
                                                  self.spr_width):
                                    self.cam[0] += 1
                                    for spr in self.all_sprites:
                                        spr.move_rect(-1, 0)
                            elif event.key == K_UP:
                                if self.cam[1] > 0:
                                    self.cam[1] -= 1
                                    for spr in self.all_sprites:
                                        spr.move_rect(0, 1)
                            elif event.key == K_DOWN:
                                if self.cam[1] < (self.env_list[0].size -
                                                  self.spr_height):
                                    self.cam[1] += 1
                                    for spr in self.all_sprites:
                                        spr.move_rect(0, -1)
            #see if all are dead
            for env in self.env_list:
                if len(env.tako_list) == 0:
                    end = True
                    print("Tako are dead :(")
            if end == True:
                for env in self.env_list:
                    if self.export_all:
                        export(dead_tako, self.filename)
                    if collect_data:
                        if len(dead_tako) > 0:
                            write_csv(self.filename, i, dead_tako)
                    return
            #let experiment go a step
            for task in self.task_list:
                task.interact_and_learn()
            if garden_mode == "Changing":
                if self.stepid > 0 and self.stepid % 100000 == 0:
                    for env in self.env_list:
                        env.switch_grasses()
            elif garden_mode == "Nutrition":
                if self.stepid > 0 and self.stepid % 40000 == 0:
                    for env in self.env_list:
                        env.switch_nutrition()
            #see if any are dead
            for env in self.env_list:
                for tak in env.tako_list:
                    if tak.dead == True:
                        env.garden_map[tak.y][tak.x] = Dirt(display_on,
                                                            tak.x, tak.y)
                        env.tako_list.remove(tak)
                        if collect_data or self.export_all:
                            dead_tako.append([tak, self.stepid, env.env_id])
                        tak.kill()
            #then check for migration
            if self.two_envs:
                if self.migration_rate > 0 and self.stepid > 0:
                    if self.stepid % 50000 == 0:
                        self.migrate(display_on)
            #check if we are doing data collection output this tick
            if self.stepid % 3000 == 0:
                if self.export_all:
                    export(dead_tako, self.filename)
                if collect_data:
                    write_csv(self.filename, i, dead_tako)
            #now, update sprites, then draw them if using graphics
            for env in self.env_list:
                if env.new_sprites != []:
                    self.get_new(env)
            self.widget_sprites.update()
            for env in self.env_list:
                for tak in env.tako_list:
                    tak.update()
            if display_on:
                self.graphics_loop(font)
            self.stepid += 1
            
    #initializes pygame sprite groups at beginning of experiment
    def load_sprites(self):
        self.widget_sprites = pygame.sprite.Group()
        env = self.env_list[self.current_env]
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

    #adds new sprites/objects to groups when environments make them
    def get_new(self, env):
        for sprite in env.new_sprites:
            if not isinstance(sprite, Dirt):
                if not isinstance(sprite, tako.Tako):
                    self.widget_sprites.add(sprite)
                else:
                    self.all_sprites.add(sprite)
            env.new_sprites.remove(sprite)

    #initializes a tiled background of dirt sprites when graphics are on
    def make_background(self):
        for x in range(self.env_list[0].size):
            for y in range(self.env_list[0].size):
                img = load_image("dirt.png")[0]
                self.background.blit(img, (x*50, y*50))

    #control loop for drawing all graphics & text when graphics are on
    def graphics_loop(self, font):
        self.screen.blit(self.background, (0, 0))
        if not self.scroll:
            self.all_sprites.draw(self.screen)
        else:
            self.draw_onscreen()
        #oh, and display which step we're on
        if pygame.font:
            text = font.render(str(self.stepid), 1, (255, 255, 255))
            textpos = text.get_rect(centerx = int(
                                        (self.screen.get_width() * 0.5)))
            self.screen.blit(text, textpos)
        pygame.display.flip()
        #cap at x fps
        self.clock.tick(self.max_fps)

    #draws graphics when they are turned on
    def draw_onscreen(self):
        for spr in self.all_sprites:
            if spr.x >= self.cam[0] and spr.x <= (self.cam[0] + self.spr_width):
                if spr.y >= self.cam[1] and spr.y <= (self.cam[1]
                                                      + self.spr_height):
                    self.screen.blit(spr.image, spr.rect)

    #migrates agents between the two environments
    #runs every 50k time-steps
    def migrate(self, display_on):
        from_0 = random.sample(self.env_list[0].tako_list,
                               int(self.migration_rate * len(
                                   self.env_list[0].tako_list)))
        from_1 = random.sample(self.env_list[1].tako_list,
                       int(self.migration_rate*len(
                           self.env_list[1].tako_list)))
        for t in from_0:
            self.env_list[0].tako_list.remove(t)
            self.env_list[1].garden_map[t.y][t.x] = Dirt(display_on,
                                                              t.x, t.y)
            self.env_list[1].add_creature(t)
        for t in from_1:
            self.env_list[1].tako_list.remove(t)
            self.env_list[0].garden_map[t.y][t.x] = Dirt(display_on,
                                                              t.x, t.y)
            self.env_list[0].add_creature(t)

#pygame function to load pngs from the img folder
def load_image(name, colorkey=None):
    fullname = os.path.join('img', name)
    image = pygame.image.load(fullname)
    image = image.convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

#records data about an agent to a csv file on the agent's death
#filename: (str) previously defined filename for output
#i: (int) current iteration
#q: (queue) queue of agents to write to csv
#   with entries in the format of a list: [agent, step_id, env_id]
def write_csv(filename, i, q):  
    with open(os.path.join("Data", filename), 'a', newline='') as csvfile:
        writ = csv.writer(csvfile)
        j = 0
        k = len(q)
        while j < k:
            l = q.popleft()
            tak = l[0]
            #puts most important/salient points of info for health/phenotype
            #genomes - ident for health genes, weight for phenotype genes -
            #into lists for output
            healthchr_a = []
            healthchr_b = []
            if isinstance(tak.genome, tg.health_genome):
                for a in tak.genome.healthchr_a:
                    healthchr_a.append(a.ident)
                for b in tak.genome.healthchr_b:
                    healthchr_b.append(b.ident)
            pref = None
            if isinstance(tak.genome, tg.phen_genome):
                pref = [tak.genome.phen_gene_a.weight,
                        tak.genome.phen_gene_b.weight,
                        tak.pref]
            #first generation has 'str' parents rather than agent parents
            if tak.gen != 0:
                parents0 = tak.parents[0].ident
                parents1 = tak.parents[1].ident
            else:
                parents0 = tak.parents[0]
                parents1 = tak.parents[1]
            writ.writerow([i, l[2], tak.ident, parents0, parents1,
                           tak.age, tak.gen, len(tak.children),
                           tak.mating_attempts, tak.accum_pain, tak.cod,
                           l[1], tak.genome.mut_record, tak.parent_degree,
                           tak.parent_genoverlap,
                           (tak.genome.disorder_count if \
                            isinstance(tak.genome, tg.health_genome)\
                            else ""),
                           healthchr_a, healthchr_b, pref])
            j += 1   
            
#exports condensed version of weight genes to a collective csv file in \Data
#one line for haploid agents, two for diploid
#each row contains the variable info for each of the agent's weight genes
#n.b. expects a standard genome layer layout to work properly
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
#makes the headers for each gene in the genome for the gene export CSV file
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
#max_steps (int): limit to x steps (<= 0 interpreted as 'until all dead')
#display_on (bool): if false, does not display anything; otherwise, runs
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
#hla_genes (int): # of HLA-inspired genes in health chromosomes
#binary_health (int): # of binary genetic disorder genes in health chromosomes
#carrier_percentage (int): % chance for an initial agent to be a disorder
#                           carrier for every given health gene (binary only)
#two_envs (bool): when True, two separate environments are created
#diff_envs (bools): when True and when two_envs is True, each env has
#                   a different food source
#migration_rate (float): when True and when two_envs is true, the migration
#                       rate b/w the two environments (done every 50k steps)
#phen_pref (bool): when True, gives agents evolving phenotype
#                       match preference
def run_experiment(x_loops=15, max_steps=0, display_on=True, max_fps=10,
                   garden_size=8, tako_number=1, pop_max=30, max_width=1800,
                   max_height=900, collect_data=True, export_all=False,
                   rand_nets=False, max_gen = 505, genetic_mode="Plain",
                   learning_on=False, seeds=None, garden_mode="Diverse Static",
                   family_detection=None, family_mod=0, record_inbreeding=True,
                   inbreed_lim = 1.1, hla_genes=0, binary_health=0,
                   carrier_percentage=40, two_envs=False, diff_envs=False,
                   migration_rate=0, phen_pref=False, filename=""):
    #round width/height down to nearest multiple of 50 if need be
    if max_width % 50 != 0:
        max_width = max_width - (max_width % 50)
    if max_height % 50 != 0:
        max_height = max_height - (max_height % 50)

    i = 0
    #create csv files if they don't already exist
    if collect_data or export_all:
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
                    writ.writerow(['iteration', 'env #', 'ID', 'parent1',
                                   'parent2', 'age', 'generation', '# children',
                                   'mating attempts', 'accum pain',
                                   'cause of death', 'timestep', 'mutations',
                                   'parent_degree', 'parent_genoverlap',
                                   '# disorders',
                                   'health a', 'health b', 'preference'])
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
    tako.phen_pref = phen_pref
    gt.phen_pref = phen_pref
    
    loop_limit = x_loops
    if loop_limit < 1:
        loop_limit = 1

    if seeds == None:
        seeds = [None for i in range(x_loops)]

    while loop_limit > 0:
        #check if seeds is long enough
        if len(seeds) < loop_limit + i:
            for j in range(loop_limit + i - len(seeds)):
                seeds.append(seeds[j])
        if seeds[0] != None:
            tako.set_seed(seeds[i])
        g = garden_game(garden_size, tako_number, pop_max, max_width,
                        max_height, display_on, max_fps, learning_on,
                        genetic_mode, rand_nets, garden_mode, filename,
                        export_all, family_mod, family_detection,
                        two_envs, diff_envs, migration_rate,
                        seeds[i])
        if display_on:
            main_window = g
            main_window.main_loop(max_steps, max_gen, display_on,
                                  collect_data, garden_mode, i)
        else:
            g.main_loop(max_steps, max_gen, display_on, collect_data,
                        garden_mode, i)
        loop_limit -= 1
        i += 1

#takes a filename (f), uses it to set user settings, and runs the experiments
#defined by f
def run_from_file(f):
    #set defaults
    x_loops=1;max_steps=0;display_on=True;max_fps=10;garden_size=13;tako_number=20
    pop_max=40;max_width=1800;max_height=900;collect_data=True;export_all=False
    rand_nets=False;max_gen=0;genetic_mode="Plain";learning_on=False
    seeds=None;garden_mode="Diverse Static";family_detection=None;family_mod=0
    record_inbreeding=True;inbreed_lim=1.1;filename="default file"
    hla_genes=0;binary_health=0;carrier_percentage=40;two_envs=False
    diff_envs=False;migration_rate=0;phen_pref=False

    
    atr_dict = {"x_loops": x_loops, "max_steps": max_steps,
                "display_on": display_on, "max_fps": max_fps,
                "garden_size": garden_size,
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
                "carrier_percentage": carrier_percentage,
                "two_envs": two_envs, "diff_envs": diff_envs,
                "migration_rate": migration_rate, "phen_pref": phen_pref}
    
    ints = ["x_loops", "max_steps", "garden_size", "tako_number", "pop_max",
            "max_width", "max_height", "max_gen", "hla_genes",
            "binary_health", "carrier_percentage", "max_fps"]
    floats = ["family_mod", "inbreed_lim", "migration_rate"]
    strs = ["genetic_mode", "garden_mode", "filename"]
    bools = ["display_on", "collect_data", "export_all", "rand_nets",
             "learning_on", "record_inbreeding", "two_envs", "diff_envs",
             "phen_pref"]

    #then sets all user-defined settings from the file f
    with open(f) as exp_file:
        for line in exp_file:
            #comments
            if line[0] == "#":
                pass
            #blank line = run what we have, then continue
            #to read the file for a new set of parameters
            elif line == "\n":
                run_experiment(atr_dict["x_loops"], atr_dict["max_steps"],
                               atr_dict["display_on"], atr_dict["max_fps"],
                               atr_dict["garden_size"],
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
                               atr_dict["filename"],
                               atr_dict["two_envs"],
                               atr_dict["diff_envs"],
                               atr_dict["migration_rate"],
                               atr_dict["phen_pref"])
                #reset defaults
                atr_dict = {"x_loops": x_loops, "max_steps": max_steps,
                    "display_on": display_on, "max_fps": max_fps,
                    "garden_size": garden_size,
                    "tako_number": tako_number, "pop_max": pop_max,
                    "max_width": max_width, "max_height": max_height,
                    "collect_data": collect_data, "export_all": export_all,
                    "rand_nets": rand_nets, "max_gen": max_gen,
                    "genetic_mode": genetic_mode, "learning_on": learning_on,
                    "seeds": seeds, "garden_mode": garden_mode,
                    "family_detection": family_detection,
                    "family_mod": family_mod,
                    "record_inbreeding": record_inbreeding,
                    "inbreed_lim": inbreed_lim, "filename": filename,
                    "hla_genes": hla_genes, "binary_health": binary_health,
                    "carrier_percentage": carrier_percentage,
                    "two_envs": two_envs, "diff_envs": diff_envs,
                    "migration_rate": migration_rate, "phen_pref": phen_pref}
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
    run_experiment(atr_dict["x_loops"], atr_dict["max_steps"],
                   atr_dict["display_on"], atr_dict["max_fps"],
                   atr_dict["garden_size"],
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
                   atr_dict["two_envs"], atr_dict["diff_envs"],
                   atr_dict["migration_rate"], atr_dict["phen_pref"],
                   atr_dict["filename"])
    
       
if __name__ == "__main__":
    run_from_file('run params example.txt')
