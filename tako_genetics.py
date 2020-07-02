import sys
sys.path.append('..')
from dgeann import dgeann
import random
import copy

#this is used by determine_mutation for health genes only
#1 is probability of a flip mutation (A>B, etc)
#2 is probability of a mutation rate mutation
health_mut_probs = (0.80, 0.20)

#extends DGEANN diploid genome to deal with a third 'health' chromosome
class health_genome(dgeann.genome):
    
    def __init__(self, layerchr_a, layerchr_b, weightchr_a, weightchr_b,
                 healthchr_a, healthchr_b, outs, mut_record):
        super().__init__(layerchr_a, layerchr_b, weightchr_a, weightchr_b)
        self.healthchr_a = healthchr_a
        self.healthchr_b = healthchr_b
        self.disorder_count = 0
        self.outs = outs
        self.mut_record = mut_record
        
    def recombine(self, other_genome):
        c = super().recombine(other_genome)
        healthchr_a = self.health_cross()
        healthchr_b = other_genome.health_cross()
        child = health_genome(c.layerchr_a, c.layerchr_b, c.weightchr_a,
                             c.weightchr_b, healthchr_a, healthchr_b, c.outs,
                             c.mut_record)
        child.mutate()
        return child

    def health_cross(self):
        l = len(self.healthchr_a) - 1
        cross = random.randint(0, l)
        new_health_a = []
        new_health_b = []
        for i in range(cross):
            new_health_a.append(copy.copy(self.healthchr_a[i]))
            new_health_b.append(copy.copy(self.healthchr_b[i]))
        for i in range(cross, len(self.healthchr_a)):
            new_health_b.append(copy.copy(self.healthchr_a[i]))
            new_health_a.append(copy.copy(self.healthchr_b[i]))
        return random.choice((new_health_a, new_health_b))

    def build(self, delete=True):
        for i in range(len(self.healthchr_a)):
            res = self.healthchr_a[i].read(None, self.healthchr_b[i], None)
            if res == False:
                self.disorder_count += 1
        return super().build(delete)

    def mutate(self):
        #super has already done mutations, so just the health chromosomes
        for g in self.healthchr_a:
            result = g.mutate()
            if result is not "":
                self.handle_mutation(result, g, "a", self.healthchr_a)
        for g in self.healthchr_b:
            result = g.mutate()
            if result is not "":
                self.handle_mutation(result, g, "b", self.healthchr_b)

    #helper function for mutate that implements gene changes from mutations                
    def handle_mutation(self, result, gene, c, chro):
        if dgeann.record_muts:
            self.mut_record.append([c, gene.ident, result])
            val = result[(result.index(",") + 2)::]
        #change mutation rate
        if result[0:3] == "Rat":
            val = float(val)
            gene.mut_rate += val
            if gene.mut_rate > 1:
                gene.mut_rate = 1
            elif gene.mut_rate < 0:
                gene.mut_rate = 0
        #flip A tp B or B to A
        elif result[0:3] == "Fli":
            if gene.dom == 1:
                gene.dom = 5
                gene.ident = "*A"
            else:
                gene.dom = 1
                gene.ident = "*B"

class health_gene(dgeann.gene):

    def __init__(self, dom, can_mut, can_dup, mut_rate, ident):
        super().__init__(dom, can_mut, False, mut_rate, ident)
        

class hla_gene(health_gene):

    def __init__(self, dom, can_mut, can_dup, mut_rate, ident):
        super().__init__(dom, can_mut, False, mut_rate, ident)

    def read(self, active_list, other_gene, read_file):
        if self.ident == other_gene.ident:
            return False
        else:
            return True

class binary_gene(health_gene):

    def __init__(self, dom, can_mut, can_dup, mut_rate, ident):
        super().__init__(dom, can_mut, False, mut_rate, ident)

    def read(self, active_list, other_gene, read_file):
        if self.dom == 1 and other_gene.dom == 1:
            return False
        else:
            return True

    def mutate(self):
        if not self.can_mut:
            return ""
        else:
            roll = random.random()
            if roll > self.mut_rate:
                return ""
            else:
                result = self.determine_mutation()
                return result

    def determine_mutation(self):
        roll = random.random()
        if roll < health_mut_probs[0]:
            #flip allele
            result = "Flip, " + self.ident
        else:
            #change mutation rate
            change = 0
            while change == 0:
                change = random.gauss(0, dgeann.sigma)
                while change + self.mut_rate > 1 or change + self.mut_rate <= 0:
                    change = random.gauss(0, dgeann.sigma)
            result = "Rate, " + str(change)
        return result
