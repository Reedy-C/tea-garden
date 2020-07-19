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
import tako_genetics as tg

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

#can be set to False
#if True, records the genetic overlap and degree of relationship b/w parents
record_inbreeding = True

#can be set to float b/w 0 and 1
#where if an agent's parents' genetic overlap is >= to inbred_lim
#it is considered to be too inbred and dies
#more nuanced approach to come
inbreed_lim = 1.1

#can be set from 0 to n
#control number of each kind of health genes
hla_genes = 0
binary_health = 0
#set from 0 to 100
#control number of carriers for each recessive binary health gene if in use
carrier_percentage = 40
#sets whether evolving phenotype match is on or not
phen_pref = False

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

    #gen is short for generation, not genome
    def __init__(self, dire, display_off, x, y, genome, ident, solver=None,
                 parents=[], gen=0, parent_degree=None, parent_genoverlap=None):
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
        self.parents = parents
        self.parent_degree = parent_degree
        self.parent_genoverlap = parent_genoverlap
        #and all the other relatives
        self.children = []
        if family_detection == "Degree" or record_inbreeding:
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
        self.accum_pain = 0
        
        if (self.parent_genoverlap != None and
            self.parent_genoverlap >= inbreed_lim):
            self.ident = dgeann.genome.network_ident()
            self.cod = "Inbred"
            self.dead = True
        else:
            self.dead = False
            self.cod = None
            if solver != None:
                self.solver = solver
                self.ident = ident
            else:
                self.solver = self.genome.build()
                #used for determining how early disordered agents die
                if ident == None:
                    self.ident = self.genome.ident
                else:
                    self.ident = ident
            if isinstance(self.genome, tg.health_genome):
                if self.genome.disorder_count > 0:
                    self.g = self.genome.disorder_count * 3
                else:
                    self.g = 1
            else:
                self.g = 1
            if isinstance(self.genome, tg.phen_genome):
                self.pref = self.genome.pref
            else:
                self.pref = None
            if phen_pref:
                self.expressed = None
                self.phen_dict = {}
            self.data = self.solver.net.blobs['data'].data
            self.stm_input = self.solver.net.blobs['stm_input'].data
        
    #gen_type can be "Diverse", "Plain", or "Haploid"
    #Diverse = diploid, two chromosomes are different
    #Plain = diploid, two chromosomes are the same
    #rand_net (bool) overrides this and creates a genome from a random starting
    #   network in the 'plain' style
    @staticmethod
    def default_tako(direction, display_off, x, y, gen_type, rand_net):
        parents = []
        #do health genes if necessary
        if hla_genes > 0 or binary_health > 0:
            healtha = []
            healthb = []
            #currently going with six alleles for HLA
            if hla_genes > 0:
                healthdict = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F"}
                for i in range(hla_genes):
                    r = random.randint(1, 6)
                    aident = healthdict[r]
                    bident = aident
                    while bident == aident:
                        r = random.randint(1, 6)
                        bident = healthdict[r]
                    healtha.append(tg.hla_gene(3, False, False, 0, aident))
                    healthb.append(tg.hla_gene(3, False, False, 0, bident))
            if binary_health > 0:
                for i in range(binary_health):
                    r = random.randint(1, 100)
                    #carrier
                    if r < carrier_percentage:
                        if random.randint(1, 2) == 1:
                            healtha.append(tg.binary_gene(1, True, False,
                                                          0.01, "*B"))
                            healthb.append(tg.binary_gene(5, True, False,
                                                          0.01, "*A"))
                        else:
                            healthb.append(tg.binary_gene(1, True, False,
                                                          0.01, "*B"))
                            healtha.append(tg.binary_gene(5, True, False,
                                                          0.01, "*A"))
                    #not a carrier, homozygous for dominant
                    else:
                        healtha.append(tg.binary_gene(5, True, False,
                                                          0.01, "*A"))
                        healthb.append(tg.binary_gene(5, True, False,
                                                          0.01, "*A"))
        #do phenotype preference gene if necessary
        if phen_pref:
            a = round(random.uniform(-1, 1), 2)
            b = round(random.uniform(-1, 1), 2)
            phen_gene_a = tg.phen_gene(random.randint(1, 5), True, False,
                                       0.01, a, str(a))
            phen_gene_b = tg.phen_gene(random.randint(1, 5), True, False,
                                       0.01, b, str(b))
        #now all the genes for the network structure
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
        #genes for network weights
        if not rand_net:
            fields = ['dom', 'can_mut', 'can_dup', 'mut_rate', 'ident',
                      'weight', 'in_node', 'out_node', 'in_layer', 'out_layer']
            filenamea = random.randint(1, 26)
            filenamea = os.path.join("Default Genetics", str(filenamea) + ".csv")
            parents.append(filenamea[:-4])
            filenameb = random.randint(1, 26)
            filenameb = os.path.join("Default Genetics", str(filenameb) + ".csv")
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
                if phen_pref and hla_genes == 0 and binary_health == 0:
                    default_genome = tg.phen_genome(layersa, layersb,
                                                    weightsa, weightsb,
                                                    phen_gene_a, phen_gene_b,
                                                    None, [])
                elif phen_pref and (hla_genes > 0 or binary_health > 0):
                    default_genome = tg.health_phen_genome(layersa, layersb,
                                                      weightsa, weightsb,
                                                      healtha, healthb,
                                                      phen_gene_a, phen_gene_b,
                                                      None,[])
                elif not phen_pref and (hla_genes > 0 or binary_health > 0):
                    default_genome = tg.health_genome(layersa, layersb,
                                                      weightsa, weightsb,
                                                      healtha, healthb, None,
                                                      [])
                else:
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
            if self.dez == 1005.0:
                self.dez = 0.0
            #this makes a wave between 0 and 150 with a period of ~1005 ticks
            self.desire = (math.sin((self.dez/160.0)+11.0)*75.0)+75.0
            if not self.display_off:
                self.update_sprite()
            self.accum_pain += self.pain
            self.accum_pain -= self.amuse/15

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
                Tako.mated_opcost(self)
                return[("amuse", -30)]
        if tak.desire >= 100:
            if self.desire >= 100:
                #if phenotype matching preferences are on
                if phen_pref:
                    match = self.compare_phenotypes(tak)
                    chance = 0.5+(0.5*(-1 + match*2)*self.pref)
                    if random.random() <= chance:
                        #success!
                        self.dez = 0
                        self.desire = 0
                        tak.dez = 0
                        tak.desire = 0
                        return [("amuse", 45), ("fullness", -10),
                                ("desire", -150)]
                    else:
                        return ("amuse", -1)
                #else just go as normal
                else:
                    self.dez = 0
                    self.desire = 0
                    tak.dez = 0
                    tak.desire = 0
                    return [("amuse", 45), ("fullness", -10), ("desire", -150)]
            else:
                return ("amuse", -1)
        else:
            return ("amuse", -1)
            Tako.mated_opcost(self)

    #creates the opportunity cost of mating
    #occurs if top-down incest avoidance is turned on and an agent
    #attempts to mate with a relative, for that agent only;
    #also occurs under all settings if an agent fails an attempt to mate
    #with another agent
    #essentially moves it down the desire function curve
    def mated_opcost(tak):
        if tak.dez < 502:
            tak.dez -= 100
            if tak.dez < 0:
                tak.dez += 1000
        else:
            if tak.dez >= 799:
                tak.dez -= 100
            else:
                tak.dez = 698

    #helper function for mated
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
    #also currently assumes everyone has the same-sized genome on both strands
    def genoverlap(self, tak):
        overlap = 0
        tot = 0
        ident_list = []
        for g in range(len(tak.genome.weightchr_a)):
            gens = [round(self.genome.weightchr_a[g].weight, 2),
                    round(self.genome.weightchr_b[g].weight, 2)]
            if round(tak.genome.weightchr_a[g].weight, 2) in gens:
                gens.remove(round(tak.genome.weightchr_a[g].weight, 2))
                overlap += 1
            if round(tak.genome.weightchr_b[g].weight, 2) in gens:
                overlap += 1
            tot += 2
        return (overlap/tot)

    #helper function for mated when phenotype matching preferences is True
    #gets all expressions of weight/health/pref
    #(not the underlying genes!)
    def get_expressed(self):
        e = []
        #easiest to grab weights directly from net
        for i in range(5):
            for j in range(18):
                e.append(round(self.solver.net.params["evo"][0].data[i][j], 2))
        for i in range(6):
            for j in range(5):
                e.append(round(self.solver.net.params["action"][0].data[i][j],
                               2))
        #next health if applicable
        if hla_genes > 0 or binary_health > 0:
            for i in range(len(self.genome.healthchr_a)):
                e.append(self.genome.healthchr_a[i].read(None,
                                                self.genome.healthchr_b[i],
                                                         None))
        #can only get here if phen_genes exist, so add that in any case
        e.append(self.pref)
        self.expressed = e
            
    #helper function for mated when phenotype matching preferences is True
    #simply gets the percentage overlap between the two phenotypes
    def compare_phenotypes(self, tak):
        if self.expressed == None:
            self.get_expressed()
        if tak.expressed == None:
            tak.get_expressed()
        if tak.ident in self.phen_dict:
            return self.phen_dict[tak.ident]
        matches = 0
        for i in range(len(self.expressed)):
            if self.expressed[i] == tak.expressed[i]:
                matches += 1
        #120 sets of weight genes + # health genes + 1 pref gene
        m = matches/(120 + hla_genes + binary_health + 1)
        self.phen_dict[tak.ident] = m
        tak.phen_dict[self.ident] = m
        return m

    #I didn't want to assign a death age at birth
    #and wanted a skewed normal distribution (as humans have)
    #(possibly other animals, but for some reason
    #those stats are harder to find)
    #average age at death should be somewhere near 100000 ticks
    #this number was based on Tako starvation time
    #by comparing ratios of starvation time/average lifespan
    #across a few species
    #self.g is the count of genetic disorders the agent has * 3
    def check_death(self):
        if self.age + (self.accum_pain) > (130000/(self.g**2)) or \
           self.age > (130000/(self.g ** 2)):
            self.cod = "old age"
            self.dead = True
        else:
            chance = self.skew_norm_pdf(self.age + self.accum_pain,
                                        (115000/(self.g**2)),
                                        (10000.0/(self.g**2)), -4)
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

    def setup(self, bottom, top):
        self.blobs.add_blob(6)
        top[0].reshape(*bottom[0].data.shape)
        self.act = bottom[0].data[0]
        self.ftop = top[0].data[0]

    def forward(self, bottom, top):
        #action # is fed directly in
        action = self.act[0]
        #this was used for learning
        #currently not used
        #if action >= 0:
        for n in (0, 1, 2, 3, 4, 5):
            if n == action:
                #means that this was the selected action
                self.ftop[n] += 1
            else:
                #if not selected action, decay the memory
                self.ftop[n] = self.ftop[n]/2 if self.ftop[n] >= .2 else 0

    def backward(self, top, propagate_down, bottom):
        pass

    def reshape(self, bottom, top):
        pass   
