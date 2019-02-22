from widget import Widget
import scipy
import math
import caffe
import random
from pygame import sprite, Color, Rect
import os
from textwrap import dedent
import sys
import csv
sys.path.append('..')
from dgeann import dgeann

rand_nets = False
dele = True
dgeann.layer_dict["STMlayer"] = '''\
                                    layer {{
                                      name: "{0.ident}"
                                      type: "Python"
                                      bottom: "{0.inputs[0]}"
                                      top: "{0.ident}"
                                      python_param {{
                                        module: "tako"
                                        layer: "STMlayer"
                                      }}
                                    }}
                                    '''

#used for family detection - moderates the chance of mating with relatives
#should be between 0 and 1
family_mod = 0
#determines if or which family detection is used
#possible values: Degree (finds degree separation of relatives)
#Genoverlap (how much do their weight genes overlap?)
#None (disables)
family_detection = None

def set_seed(seed):
    random.seed(seed)
    dgeann.random.seed(seed)

# a Tako is a creature and also a Widget
# it has a neural net
# it has a genome
# it has drives (amuse, fullness, etc)
# it is meant to live in a Garden
class Tako(Widget):
    node = 4
    dir_map = {0: "north.png", 1: "east.png", 2: "south.png", 3: "west.png"}

    #gen is short for generation, not genome or the like
    def __init__(self, dire, display_off, x, y, genome, ident, solver=None,
                 parents=[], gen=0):
        sprite.Sprite.__init__(self)
        self.direction = dire
        self.x = x
        self.y = y
        self.genome = genome
        self.display_off = display_off
        if not display_off:
            self.image, self.rect = self.load_image(self.dir_map[dire],
                                                Color('#FF00FF'))
        self.rect = Rect(x*50, y*50, 50, 50)
        self.fullness = 150
        self.amuse = 150
        self.pain = 0
        self.desire = 0.0
        self.last_fullness = 150
        self.last_amuse = 150
        self.last_pain = 0
        self.last_desire = 0
        self.last_obj = None
        self.last_action = -1
        self.age = 0
        self.dez = 0
        self.dead = False
        self.parents = parents
        #and all the other relatives
        self.children = []
        if family_detection == "Degree":
            self.siblings = []
            self.half_siblings = []
            self.niblings = []
            self.auncles = []
            self.double_cousins = []
            self.cousins = []
            self.grandchildren = []
            self.grandparents = []
            self.half_niblings = []
            self.half_auncles = []
            self.great_grandchildren = []
            self.great_grandparents = []
            self.great_niblings = []
            self.great_auncles = []
            if type(parents[0]) != str:
                parents[0].degree_setting(parents[1], self)

        self.fam_dict = {}
        
        self.gen = gen
        self.mating_attempts = 0
        self.cod = None
        if solver != None:
            self.solver = solver
            self.ident = ident
        else:
            self.solver = self.genome.build()
            if ident == None:
                self.ident = self.genome.ident
            else:
                self.ident = ident
        self.data = self.solver.net.blobs['data'].data
        self.stm_input = self.solver.net.blobs['stm_input'].data
        
    #gen_type can be "Diverse", "Plain", or "Haploid"
    #Diverse = two chromosomes are different
    #Plain = two chromosomes are the same
    #rand_net (bool) overrides this and creates a genome from a random starting
    #   network in the 'plain' style (except for random dominance)
    @staticmethod
    def default_tako(direction, display_off, x, y, gen_type, rand_net):
        parents = []
        data = dgeann.layer_gene(5, False, False, 0, "data",
                                        [], 12, "input")
        stm_input = dgeann.layer_gene(5, False, False, 0, "stm_input",
                                             [], 6, "input")
        stm = dgeann.layer_gene(5, False, False, 0, "STM",
                                       ["stm_input"], 6, "STMlayer")
        evo = dgeann.layer_gene(3, False, False, 0.1, "evo",
                                ["data", "STM"], 5, "IP")
        action = dgeann.layer_gene(5, False, False, 0, "action",
                                          ["evo"], 6, "IP")
        layersa = [data, stm_input, stm, evo, action]
        layersb = [data, stm_input, stm, evo, action]
        weightsa = []
        weightsb = []
        if not rand_net:
            fields = ['dom', 'can_mut', 'can_dup', 'mut_rate', 'ident',
                      'weight', 'in_node', 'out_node', 'in_layer', 'out_layer']
            l = random.randint(1, 18)
            m = random.randint(0, 1)
            if m == 0:
                filenamea = "Default Genetics/" + str(l) + "_a.csv"
            else:
                filenamea = "Default Genetics/" + str(l) + "_b.csv"
            parents.append(filenamea[:-4])
            l = random.randint(1, 18)
            m = random.randint(0, 1)
            if m == 0:
                filenameb = "Default Genetics/" + str(l) + "_a.csv"
            else:
                filenameb = "Default Genetics/" + str(l) + "_b.csv"
            with open(filenamea, newline="") as file:
                r = csv.DictReader(file, fieldnames = fields)
                for row in r:
                    in_node = int(row['in_node'])
                    w = dgeann.weight_gene(int(row['dom']),
                                           bool(row['can_mut']),
                                           bool(row['can_dup']),
                                           float(row['mut_rate']),
                                           row['ident'], float(row['weight']),
                                           in_node, int(row['out_node']),
                                           row['in_layer'], row['out_layer'])
                    weightsa.append(w)
            if gen_type == "Diverse":
                parents.append(filenameb[:-4])
                with open(filenameb, newline="") as file:
                    r = csv.DictReader(file, fieldnames = fields)
                    for row in r:
                        in_node = int(row['in_node'])
                        w = dgeann.weight_gene(int(row['dom']),
                                               bool(row['can_mut']),
                                               bool(row['can_dup']),
                                               float(row['mut_rate']),
                                               row['ident'], float(row['weight']),
                                               in_node, int(row['out_node']),
                                               row['in_layer'], row['out_layer'])
                        weightsb.append(w)
            elif gen_type == "Plain":
                parents.append(filenamea[:-4])
                #copy the first strand again
                #slightly faster than a deepcopy
                with open(filenamea, newline="") as file:
                    r = csv.DictReader(file, fieldnames = fields)
                    for row in r:
                        in_node = int(row['in_node'])
                        w = dgeann.weight_gene(int(row['dom']),
                                           bool(row['can_mut']),
                                           bool(row['can_dup']),
                                           float(row['mut_rate']),
                                           row['ident'], float(row['weight']),
                                           in_node, int(row['out_node']),
                                           row['in_layer'], row['out_layer'])
                        weightsb.append(w)
            if gen_type != "Haploid":
                default_genome = dgeann.genome(layersa, layersb,
                                               weightsa, weightsb)
            else:
                default_genome = dgeann.haploid_genome(layersa, weightsa)
        else:
            default_genome = dgeann.genome(layersa, layersb, [], [])
            parents = ["random", "random"]
        solver = default_genome.build(delete=dele)
        tak = Tako(direction, display_off, x, y, default_genome,
                   default_genome.ident, solver=solver, parents=parents)
        return tak
            
    #drives go DOWN over time
    #except for desire, which has a sine wave funtion
    def update(self):
        self.age += 1
        if self.age % 1500 == 0:
            self.check_death()
        if not self.dead:
            self.last_fullness = self.fullness
            self.last_amuse = self.amuse
            self.last_pain = self.pain
            self.last_desire = self.desire
            self.fullness -= 0.5
            if self.fullness <= 0:
                self.cod = "fullness"
                self.dead = True
            if self.amuse > 0:
                self.amuse -= 0.25
            else:
                self.amuse = 0
            if self.pain > 0:
                self.pain = self.pain*.6
                if self.pain < 1:
                    self.pain = 0
            self.dez += 1
            if self.dez == 503.0:
                self.dez = 0.0
            #this makes a wave between 0 and 150 with a period of 502 ticks
            self.desire = (math.sin((self.dez/80.0)+11.0)*75.0)+75.0
            if not self.display_off:
                self.update_sprite()

    def update_sprite(self):
        if self.last_action == 1 or self.last_action == 2:
            self.image, temp = self.load_image(self.dir_map[self.direction], -1)
        
    def update_drives(self, drive, modifier):
        if drive == "fullness":
            self.fullness += modifier
            if self.fullness > 150:
                self.fullness = 150
        elif drive == "amuse":
            self.amuse += modifier
            if self.amuse > 150:
                self.amuse = 150
        elif drive == "pain":
            self.pain += modifier
        elif drive == "desire":
            self.desire += modifier

    def modify(self, result):
        if result is not None:
            for x in range(len(result)):
                if x%2 == 0:
                    drive = result[x]
                else:
                    modifier = result[x]
                    self.update_drives(drive, modifier)

    def make_solver(self):
        ident_file = os.path.join('Gen files', self.ident)
        ident_file = ident_file + '.gen'
        result = dedent('''\
                        net: "{0}"
                        solver_type: ADADELTA
                        momentum: 0.95
                        base_lr: 0.2
                        lr_policy: "step"
                        gamma: 0.1
                        stepsize: 1000000
                        max_iter: 2000000
                        display: 10000
                        '''.format(ident_file))
        f = open("temp_solver.txt", "w")
        f.write(result)
        f.close()
        solver = caffe.AdaDeltaSolver('temp_solver.txt')
        os.remove('temp_solver.txt')
        return solver

    def played(self):
        return ("amuse", 15)

    def mated(self, tak):
        if family_detection != None:
            relation = self.check_relations(tak)
            mate_chance = 1 - family_mod*relation
            if mate_chance <= 0:
                too_close = True
            elif mate_chance == 1:
                too_close = False
            else:
                too_close = random.random()
                if too_close < mate_chance:
                    too_close = True
                else:
                    too_close = False
            #'disgust' reaction
            if too_close:
                self.dez = 0
                self.desire = 0
                return[("amuse", -30)]
        if tak.desire >= 100:
            if self.desire >= 100:
                self.dez = 0
                self.desire = 0
                tak.dez = 0
                tak.desire = 0
                return [("amuse", 45), ("fullness", -10), ("desire", -150)]
            else:
                return ("amuse", -1)
        else:
            return ("amuse", -1)

    #returns a relatedness percentage dependent on detection mode
    def check_relations(self, tak):
        if tak.ident in self.fam_dict.keys():
            return self.fam_dict[tak.ident]
        else:
            if family_detection == "Degree":
                self.fam_dict[tak.ident] = self.degree_detection(tak)
            if family_detection == "Genoverlap":
                self.fam_dict[tak.ident] = self.genoverlap(tak)
            return self.fam_dict[tak.ident]

    #helper function for check_relationships
    #simple first/second/third degree relatives
    def degree_detection(self, other_parent):
        #first degree
        if (other_parent in self.parents or
            other_parent in self.children or
            other_parent in self.siblings):
            return 1.0
        #second degree
        elif (other_parent in self.half_siblings or
              other_parent in self.auncles or
              other_parent in self.niblings or
              other_parent in self.grandparents or
              other_parent in self.grandchildren or
              other_parent in self.double_cousins):
            return 0.5
        #third degree
        elif (other_parent in self.cousins or
              other_parent in self.great_grandparents or
              other_parent in self.great_grandchildren or
              other_parent in self.half_auncles or
              other_parent in self.half_niblings or
              other_parent in self.great_niblings or
              other_parent in self.great_auncles):
            return 0.25
        else:
            return 0.0
        
    def degree_setting(self, other_parent, baby):
        #first degree: parents already set
        #siblings/half-siblings
        for tak in self.children:
            #excluding baby?
            if tak.parents == [self, other_parent]:
                tak.siblings.append(baby)
                baby.siblings.append(tak)
            else:
                tak.half_siblings.append(baby)
                baby.half_siblings.append(tak)
            for tak in other_parent.children:
                if tak.parents != [self, other_parent]:
                    tak.half_siblings.append(baby)
                    baby.half_siblings.append(tak)
        #second degree: half-siblings (set), auncles, niblings,
        #grandparents/children, double cousins
        for tak in self.siblings:
            tak.niblings.append(baby)
            baby.auncles.append(tak)
            for cous in tak.children:
                #second degree: double cousins
                #TODO - is there a better way to do this?
                #TODO - do I need to do this on both sides?
                #seems like I shouldn't
                for par in cous.parents:
                    if par != tak:
                        if par in other_parent.siblings:
                            cous.double_cousins.append(baby)
                            baby.double_cousins.append(cous)
                        #third degree: cousins
                        else:
                            cous.cousins.append(baby)
                            baby.cousins.append(cous)
        for tak in other_parent.siblings:
            tak.niblings.append(baby)
            baby.auncles.append(tak)
            #cousins
            for cous in tak.children:
                if cous not in baby.double_cousins:
                    cous.cousins.append(baby)
                    baby.cousins.append(cous)
        for tak in self.parents:
            if type(tak) != str:
                tak.grandchildren.append(baby)
                baby.grandparents.append(tak)
                #third degree: great-grandparents/children
                for great in tak.parents:
                    if type(great) != str:
                        great.great_grandchildren.append(baby)
                        baby.great_grandparents.append(great)
                #third degree: great-auncles/niblings
                for aunc in tak.siblings:
                    aunc.great_niblings.append(baby)
                    baby.great_auncles.append(aunc)
        for tak in other_parent.parents:
            if type(tak) != str:
                tak.grandchildren.append(baby)
                baby.grandparents.append(tak)
                #great-grandparents/children
                for great in tak.parents:
                    if type(great) != str:
                        great.great_grandchildren.append(baby)
                        baby.great_grandparents.append(great)
                #great-auncles/niblings
                for aunc in tak.siblings:
                    aunc.great_niblings.append(baby)
                    baby.great_auncles.append(aunc)
        #third degree: half auncles/niblings
        for tak in self.half_siblings:
            tak.half_niblings.append(baby)
            baby.half_auncles.append(tak)
        for tak in other_parent.half_siblings:
            tak.half_niblings.append(baby)
            baby.half_auncles.append(tak)
        #first degree: children
        self.children.append(baby)
        other_parent.children.append(baby)
            
    #helper function for check_relationships
    #finds percentage of genetic overlap
    #TODO currently just doing weight genes b/c still working on layer genes
    #+then they would all look a little related 
    def genoverlap(self, tak):
        overlap = 0
        tot = 0
        ident_list = []
        for gen in tak.genome.weightchr_a:
            ident_list.append(gen.ident)
            tot += 1
        for gen in tak.genome.weightchr_b:
            ident_list.append(gen.ident)
            tot += 1
        for gen in self.genome.weightchr_a:
            if gen.ident in ident_list:
                overlap += 1
                ident_list.remove(gen.ident)
        for gen in self.genome.weightchr_b:
            if gen.ident in ident_list:
                overlap += 1
        return (overlap/tot)

    #I didn't want to assign a death age at birth
    #and wanted a skewed normal distribution (as humans have)
    #(possibly other animals, but for some reason
    #those stats are harder to find)
    #average age at death should be somewhere near 100000 ticks
    #this number was based on Tako starvation time
    #by comparing ratios of starvation time/average lifespan
    #across a few species
    def check_death(self):
        if self.age > 130000:
            self.cod = "old age"
            self.dead = True
        else:
            chance = self.skew_norm_pdf(self.age, 115000, 10000.0, -4)
            r = random.random()
            if r < chance:
                self.cod = "natural"
                self.dead = True
                
    #generates skew normal distribution
    #adapted slightly from
    #https://stackoverflow.com/questions/36200913/
    def skew_norm_pdf(self, x, e=0, w=1, a=0):
        t = (x-e) / w
        return 2.0 * scipy.stats.norm.pdf(t) * scipy.stats.norm.cdf(a*t)


class STMlayer(caffe.Layer):

    #TODO check this
    def setup(self, bottom, top):
        self.blobs.add_blob(6)
        top[0].reshape(*bottom[0].data.shape)

    def forward(self, bottom, top):
        #action # is fed directly in
        action = bottom[0].data[0][0]
        ftop = top[0].data[0]
        if action >= 0:
            for x in range(len(ftop)):
                if x == action:
                    #means that this was the selected action
                    top[0].data[0][x] += 1
                else:
                    #if not selected action, decay the memory
                    t = top[0].data[0][x]
                    if t != 0:
                        top[0].data[0][x] = self.decay(t)

    def backward(self, top, propagate_down, bottom):
        pass

    def reshape(self, bottom, top):
        pass   

    def decay(self, x):
        x = x/2
        if x < 0.1:
            x = 0
        return x
