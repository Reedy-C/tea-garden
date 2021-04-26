import sys
sys.path.append('..')
from dgeann import dgeann
import random
import copy

#this is used by determine_mutation for health genes only
#1 is probability of a flip mutation (A>B, etc)
#2 is probability of a mutation rate mutation
health_mut_probs = (0.80, 0.20)
#ditto above, except #1 is chance of a weight mutation
phen_mut_probs = (0.80, 0.20)

#extends DGEANN diploid genome to deal with a third 'health' chromosome
class health_genome(dgeann.Genome):
    
    def __init__(self, layerchr_a, layerchr_b, weightchr_a, weightchr_b,
                 healthchr_a, healthchr_b, outs, mut_record):
        dgeann.Genome.__init__(self, layerchr_a, layerchr_b, weightchr_a,
                               weightchr_b)
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
            if result != "":
                self.handle_mutation(result, g, "a", self.healthchr_a)
        for g in self.healthchr_b:
            result = g.mutate()
            if result != "":
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

class health_gene(dgeann.Gene):

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


#extends DGEANN diploid genome to allow for an evolving phenotype matching
#preference gene
class phen_genome(dgeann.Genome):

    def __init__(self, layerchr_a, layerchr_b, weightchr_a, weightchr_b,
                 phen_gene_a, phen_gene_b, outs, mut_record):
        super().__init__(layerchr_a, layerchr_b, weightchr_a, weightchr_b)
        self.outs = outs
        self.mut_record = mut_record
        self.phen_gene_a = phen_gene_a
        self.phen_gene_b = phen_gene_b

    def recombine(self, other_genome):
        c = super().recombine(other_genome)
        a = random.choice([self.phen_gene_a, self.phen_gene_b])
        b = random.choice([other_genome.phen_gene_a, other_genome.phen_gene_b])
        child = phen_genome(c.layerchr_a, c.layerchr_b, c.weightchr_a,
                     c.weightchr_b, copy.copy(a), copy.copy(b), c.outs,
                     c.mut_record)
        child.mutate()
        return child

    def mutate(self):
        resulta = self.phen_gene_a.mutate()
        resultb = self.phen_gene_b.mutate()
        if resulta != "":
            phen_genome.handle_mutation(self, resulta, "A", self.phen_gene_a)
        if resultb != "":
            phen_genome.handle_mutation(self, resultb, "B", self.phen_gene_b)

    def handle_mutation(self, result, c, gene):
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
        #change weight
        if result[0:3] == "Pre":
            val = float(val)
            gene.weight += val
            gene.weight = round(gene.weight, 2)
            if gene.weight > 1:
                gene.weight = 1
            elif gene.weight < -1:
                gene.weight = -1
            gene.ident = str(gene.weight)

    def build(self, delete=True):
        if self.phen_gene_a.dom > self.phen_gene_b.dom:
            self.pref = self.phen_gene_a.weight
        elif self.phen_gene_b.dom > self.phen_gene_a.dom:
            self.pref = self.phen_gene_b.weight
        else:
            self.pref = round((self.phen_gene_a.weight +
                               self.phen_gene_b.weight)/2, 2)
        return super().build(delete)        

class phen_gene(dgeann.Gene):

    def __init__(self, dom, can_mut, can_dup, mut_rate, weight, ident):
        super().__init__(dom, can_mut, False, mut_rate, ident)
        self.weight = weight

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
            #change weight
            w = round(random.gauss(0, .05), 3)
            while w == 0.00:
                w = round(random.gauss(0, .05), 3)
            result = "Pref, " + str(w)
        else:
            #change mutation rate
            change = 0
            while change == 0:
                change = random.gauss(0, dgeann.sigma)
                while change + self.mut_rate > 1 or change + self.mut_rate <= 0:
                    change = random.gauss(0, dgeann.sigma)
            result = "Rate, " + str(change)
        return result

class health_phen_genome(health_genome, phen_genome):
    #TODO - can any of these be simplified with super()?

    def __init__(self, layerchr_a, layerchr_b, weightchr_a, weightchr_b,
                 healthchr_a, healthchr_b, phen_gene_a, phen_gene_b,
                 outs, mut_record):
        health_genome.__init__(self, layerchr_a, layerchr_b, weightchr_a,
                               weightchr_b, healthchr_a, healthchr_b, outs,
                               mut_record)
        self.phen_gene_a = phen_gene_a
        self.phen_gene_b = phen_gene_b

    def recombine(self, other_genome):
        child = health_genome.recombine(self, other_genome)
        a = random.choice([self.phen_gene_a, self.phen_gene_b])
        b = random.choice([other_genome.phen_gene_a, other_genome.phen_gene_b])
        child = health_phen_genome(child.layerchr_a, child.layerchr_b,
                                   child.weightchr_a, child.weightchr_b,
                                   child.healthchr_a, child.healthchr_b,
                                   a, b, child.outs, child.mut_record)
        #already has health + most mutations taken care of
        phen_genome.mutate(child)
        return child

    def build(self, delete=True):
        for i in range(len(self.healthchr_a)):
            res = self.healthchr_a[i].read(None, self.healthchr_b[i], None)
            if res == False:
                self.disorder_count += 1
        return phen_genome.build(self, delete)
