import sys
sys.path.append('..')
from dgeann import dgeann
import random

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
        return health_genome(c.layerchr_a, c.layerchr_b, c.weightchr_a,
                             c.weightchr_b, healthchr_a, healthchr_b, c.outs,
                             c.mut_record)

    def health_cross(self):
        l = len(self.healthchr_a) - 1
        cross = random.randint(0, l)
        new_health_a = []
        new_health_b = []
        for i in range(cross):
            new_health_a.append(self.healthchr_a[i])
            new_health_b.append(self.healthchr_b[i])
        for i in range(cross, len(self.healthchr_a)):
            new_health_b.append(self.healthchr_a[i])
            new_health_a.append(self.healthchr_b[i])
        return random.choice((new_health_a, new_health_b))

    def build(self, delete=True):
        for i in range(len(self.healthchr_a)):
            res = self.healthchr_a[i].read(None, self.healthchr_b[i], None)
            if res == False:
                self.disorder_count += 1
        return super().build(delete)
    

#currently no mutations for health genes
class health_gene(dgeann.gene):

    def __init__(self, dom, can_mut, can_dup, mut_rate, ident):
        super().__init__(dom, False, False, 0, ident)
        

class hla_gene(health_gene):

    def __init__(self, dom, can_mut, can_dup, mut_rate, ident):
        super().__init__(dom, False, False, 0, ident)

    def read(self, active_list, other_gene, read_file):
        if self.ident == other_gene.ident:
            return False
        else:
            return True

class binary_gene(health_gene):

    def __init__(self, dom, can_mut, can_dup, mut_rate, ident):
        super().__init__(dom, False, False, 0, ident)

    def read(self, active_list, other_gene, read_file):
        if self.dom == 1 and other_gene.dom == 1:
            return False
        else:
            return True
