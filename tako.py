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

# a Tako is a creature and also a Widget
# it has a neural net
# it has a genome
# it has drives (amuse, fullness, etc)
# it is meant to live in a Garden
class Tako(Widget):
    node = 4
    dir_map = {0: "north.png", 1: "east.png", 2: "south.png", 3: "west.png"}

    #gen is short for generation, not genome or the like
    def __init__(self, dire, x, y, genome, ident, solver=None,
                 parents=[None, None], gen=0):
        sprite.Sprite.__init__(self)
        self.direction = dire
        self.x = x
        self.y = y
        self.genome = genome
        if ident != None:
            self.ident = ident
        #note to self: these three lines need to be disabled to run test suite
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
        self.children = []
        self.parents = parents
        self.gen = gen
        self.mating_attempts = 0
        self.cod = None
        if solver != None:
            self.solver = solver
        else:
            self.solver = self.genome.build()
            self.ident = self.genome.ident
        #for pr in net.params.keys():
        #    self.solver.net.params[pr][0].data[...] = net.params[pr][0].data[...]
        #do not delete; keeps synchedmem error from occuring
        #for some reason
        #TODO try putting a small pause in instead
        
    #gen_tye can be "Diverse", "Plain", or "Haploid"
    #Diverse = two chromosomes are different
    #Plain = two chromosomes are the same
    #rand_net (bool) overrides this and creates a genome from a random starting
    #   network in the 'plain' style (except for random dominance)
    @staticmethod
    def default_tako(direction, x, y, gen_type, rand_net):
        data = dgeann.layer_gene(5, False, False, 0, "data",
                                        [], 10, "input")
        #reward = dgeann.layer_gene(5, False, False, 0, "reward",
        #                                 [], 6, "input")
        #stm_input = dgeann.layer_gene(5, False, False, 0, "stm_input",
        #                                     ["data", "reward"], 6, "input")
        stm_input = dgeann.layer_gene(5, False, False, 0, "stm_input",
                                             ["data"], 6, "input")
        stm = dgeann.layer_gene(5, False, False, 0, "STM",
                                       ["stm_input"], 6, "STMlayer")
        concat = dgeann.layer_gene(5, False, False, 0, "concat_0",
                                          ["data", "STM"], None, "concat")
        evo = dgeann.layer_gene(3, False, False, 0.01, "evo",
                                ["concat_0"], 5, "IP")
        action = dgeann.layer_gene(5, False, False, 0, "action",
                                          ["evo"], 6, "IP")
        #loss = dgeann.layer_gene(5, False, False, 0, "loss",
        #                                ["action", "reward"], 6, "loss")
        #layers = [data, reward, stm_input, stm, concat, action, loss]
        layersa = [data, stm_input, stm, concat, evo, action]
        layersb = [data, stm_input, stm, concat, evo, action]
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
                weightsb = weightsa.copy()
            if gen_type != "Haploid":
                default_genome = dgeann.genome(layersa, layersb,
                                               weightsa, weightsb)
            else:
                default_genome = dgeann.haploid_genome(layersa, weightsa)
        else:
            default_genome = dgeann.genome(layersa, layersb, [], [])
        solver = default_genome.build(delete=dele)
        tak = Tako(direction, x, y, default_genome, default_genome.ident,
                   solver=solver)
        for key in tak.solver.net.params:
            print(key)
            #do not delete; keeps synchedmem error from occuring
            #for some reason
            #TODO try putting a small pause in instead
            #print(tak.solver.net.params[key][0].data)
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
        if tak.desire >= 100:
            if self.desire >= 100:
                self.dez = 0
                self.desire = 0
                tak.dez = 0
                tak.desire = 0
                return [("amuse", 45), ("fullness", -10), ("desire", -150),
                self.genome.recombine(tak.genome), [self.ident, tak.ident],
                        (max(self.gen, tak.gen) + 1)]
            else:
                return ("amuse", -1)
        else:
            return ("amuse", -1)

    #I didn't want to assign a death age at birth
    #and wanted a skewed normal distribution (as humans have)
    #(possibly other animals, but for some reason those stats are harder to find)
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

    def forward(self, bottom, top):
        #action # is fed directly in
        act = bottom[0].data.flatten()
        action = act[0]
        ftop = top[0].data.flatten()
        if action >= 0:
            for x in range(len(ftop)):
                if x == action:
                    #means that this was the selected action
                    top[0].data[0][0][0][x] += 1
                else:
                    #if not selected action, decay the memory
                    if top[0].data[0][0][0][x] != 0:
                        top[0].data[0][0][0][x] = self.decay(top[0].data[0][0][0][x])

    def backward(self, top, propagate_down, bottom):
        pass

    def reshape(self, bottom, top):
        top[0].reshape(*bottom[0].data.shape)

    def decay(self, x):
        x = x/2
        if x < 0.1:
            x = 0
        return x
