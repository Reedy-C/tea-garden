import unittest
import csv
import tako
import sys
import copy
sys.path.append('..')
from dgeann import dgeann

class testGenetics(unittest.TestCase):

    def setUp(self):
        tako.random.seed("genetics")
        self.fields = ['dom', 'can_mut', 'can_dup', 'mut_rate', 'ident',
                      'weight', 'in_node', 'out_node', 'in_layer', 'out_layer']

    #'plain' diploid
    def test_p_diploid(self):
        tak = tako.Tako.default_tako(0, False, 0, 0, "Plain", False)
        for i in range(len(tak.genome.layerchr_a)):
            self.assertEqual(tak.genome.weightchr_a[i].ident,
                             tak.genome.weightchr_b[i].ident)
            self.assertEqual(tak.genome.weightchr_a[i].in_node,
                             tak.genome.weightchr_b[i].in_node)
            self.assertEqual(tak.genome.weightchr_a[i].out_node,
                             tak.genome.weightchr_b[i].out_node)
            self.assertEqual(tak.genome.weightchr_a[i].weight,
                             tak.genome.weightchr_b[i].weight)
            self.assertEqual(tak.genome.weightchr_a[i].mut_rate,
                             tak.genome.weightchr_b[i].mut_rate)

    #'diverse' diploid
    def test_d_diploid(self):
        tak = tako.Tako.default_tako(0, False, 0, 0, "Diverse", False)
        for i in range(len(tak.genome.layerchr_a)):
            self.assertNotEqual(tak.genome.weightchr_a[i].ident,
                             tak.genome.weightchr_b[i].ident)
            self.assertEqual(tak.genome.weightchr_a[i].in_node,
                             tak.genome.weightchr_b[i].in_node)
            self.assertEqual(tak.genome.weightchr_a[i].out_node,
                             tak.genome.weightchr_b[i].out_node)
            self.assertNotEqual(tak.genome.weightchr_a[i].weight,
                             tak.genome.weightchr_b[i].weight)

    def test_haploid(self):
        tak = tako.Tako.default_tako(0, False, 0, 0, "Haploid", False)
        with open("Default Genetics/29.csv") as file:
            r = csv.DictReader(file, fieldnames=self.fields)
            i = 0
            for row in r:
                self.assertEqual(tak.genome.weightchr_a[i].ident,
                                 row['ident'])
                self.assertEqual(tak.genome.weightchr_a[i].in_node,
                                 int(row['in_node']))
                self.assertEqual(tak.genome.weightchr_a[i].mut_rate,
                                 float(row['mut_rate']))
                self.assertEqual(tak.genome.weightchr_a[i].weight,
                                 float(row['weight']))
                i += 1

    def test_randnet(self):
        tak = tako.Tako.default_tako(0, False, 0, 0, "Haploid", True)
        for i in range(len(tak.genome.weightchr_a)):
            self.assertEqual(tak.genome.weightchr_a[i].weight,
                             tak.genome.weightchr_b[i].weight)

    def test_mating(self):
        tako.family_detection = None
        tako.family_mod = 0
        tak_1 = tako.Tako.default_tako(0, False, 0, 0, "Plain", False)
        tak_2 = tako.Tako.default_tako(0, False, 0, 1, "Plain", False)
        result = tak_1.mated(tak_2)
        self.assertEqual(result, ("amuse", -1))
        tak_1.desire = 150
        result = tak_1.mated(tak_2)
        self.assertEqual(result, ("amuse", -1))
        tak_1.desire = 0
        tak_2.desire = 150
        tak_2.dez = 250
        result = tak_1.mated(tak_2)
        self.assertEqual(result, ("amuse", -1))
        tak_1.desire = 100
        tak_1.dez = 150
        result = tak_1.mated(tak_2)
        self.assertEqual(len(result), 3)
        self.assertEqual(tak_1.desire, 0)
        self.assertEqual(tak_2.desire, 0)
        self.assertEqual(tak_1.dez, 0)
        self.assertEqual(tak_2.dez, 0)
        tak_1.update()
        tak_2.update()
        tak_2.update()
        self.assertAlmostEqual(tak_1.desire, 0.004, places=2)
        self.assertAlmostEqual(tak_2.desire, 0.01, places=2)
        self.assertEqual(tak_1.dez, 1)
        self.assertEqual(tak_2.dez, 2)

    def test_genoverlap(self):
        tako.family_detection = "Genoverlap"
        tako.family_mod = 1
        tak_1 = tako.Tako.default_tako(0, False, 0, 0, "Diverse", False)
        tak_2 = copy.copy(tak_1)
        self.assertEqual(tak_1.genoverlap(tak_2), 1.0)
        self.assertEqual(tak_1.mated(tak_2), [("amuse", -30)])
        tak_3 = tako.Tako.default_tako(0, False, 0, 0, "Diverse", False)
        self.assertAlmostEqual(tak_1.genoverlap(tak_3), 0.029, 3)
        gen_4 = tak_1.genome.recombine(tak_3.genome)
        tak_4 = tako.Tako(0, False, 0, 0, gen_4, "tak_4", None,
                          [tak_1.ident, tak_3.ident], 1)
        self.assertAlmostEqual(tak_4.genoverlap(tak_1), 0.5, 1)
        self.assertAlmostEqual(tak_4.genoverlap(tak_3), 0.5, 1)
        tak_1.desire = 150
        tak_3.desire = 150
        tako.random.random()
        tako.random.random()
        gen_5 = tak_1.genome.recombine(tak_3.genome)
        tak_5 = tako.Tako(0, False, 0, 0, gen_5, "tak_5", None,
                          [tak_1.ident, tak_3.ident], 1)
        self.assertEqual(tak_5.genoverlap(tak_4), tak_4.genoverlap(tak_5))
        tak_4.desire = 150
        tak_5.desire = 150
        gen_6 = tak_5.genome.recombine(tak_4.genome)
        tak_6 = tako.Tako(0, False, 0, 0, gen_6, "tak_6", None,
                          [tak_4.ident, tak_5.ident], 1)
        self.assertAlmostEqual(tak_6.genoverlap(tak_4), 0.54, 2)

    def test_degree_setting(self):
        tako.family_detection = "Degree"
        tako.family_mod = 1
        GGP1 = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        GGP2 = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        GP2 = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        GP3 = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        GP4 = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        G5 = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        P3 = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        GA = tako.Tako(0, False, 0, 0, GGP1.genome.recombine(GGP2.genome),
                       "GA", None, [GGP1, GGP2], 1)
        GP1 = tako.Tako(0, False, 0, 0, GGP1.genome.recombine(GGP2.genome),
                        "GP1", None, [GGP1, GGP2], 1)
        A1 = tako.Tako(0, False, 0, 0, GGP1.genome.recombine(GGP2.genome), "A1",
                       None, [GP1, GP2], 1)
        A2 = tako.Tako(0, False, 0, 0, GP3.genome.recombine(GP4.genome), "A2",
                       None, [GP3, GP4], 1)
        A_M1 = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        P1 = tako.Tako(0, False, 0, 0, GP1.genome.recombine(GP2.genome),
                       "P1", None, [GP1, GP2], 1)
        P2 = tako.Tako(0, False, 0, 0, GP3.genome.recombine(GP4.genome),
                       "P2", None, [GP3, GP4], 1)
        HA = tako.Tako(0, False, 0, 0, GP4.genome.recombine(G5.genome),
                       "HA", None, [GP4, G5], 1)
        CO = tako.Tako(0, False, 0, 0, A_M1.genome.recombine(A1.genome),
                       "CO", None, [A_M1, A1], 1)
        Sib = tako.Tako(0, False, 0, 0, P1.genome.recombine(P2.genome),
                        "Sib", None, [P1, P2], 1)
        Center = tako.Tako(0, False, 0, 0, P1.genome.recombine(P2.genome),
                           "Center", None, [P1, P2], 1)
        HS = tako.Tako(0, False, 0, 0, P2.genome.recombine(P3.genome),
                       "HS", None, [P2, P3], 1)
        DC = tako.Tako(0, False, 0, 0, A1.genome.recombine(A2.genome),
                       "DC", None, [A1, A2], 1)
        Sib_m = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        Center_m = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        HS_m = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        Nib_m = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        C_m = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        GC_m = tako.Tako.default_tako(0, False, 0, 0, "Diverse", True)
        Nib = tako.Tako(0, False, 0, 0, Sib.genome.recombine(Sib_m.genome),
                        "Nib", None, [Sib, Sib_m], 1)
        C = tako.Tako(0, False, 0, 0, Center.genome.recombine(Center_m.genome),
                      "C", None, [Center, Center_m], 1)
        HNib = tako.Tako(0, False, 0, 0, HS.genome.recombine(HS_m.genome),
                         "HNib", None, [HS, HS_m], 1)
        GNib = tako.Tako(0, False, 0, 0, Nib.genome.recombine(Nib_m.genome),
                         "GNib", None, [Nib, Nib_m], 1)
        GC = tako.Tako(0, False, 0, 0, C.genome.recombine(C_m.genome), "GC",
                       None, [C, C_m], 1)
        GGC = tako.Tako(0, False, 0, 0, GC.genome.recombine(GC_m.genome), "GGC",
                        None, [GC, GC_m], 1)
        self.assertEqual(Center.children, [C])
        self.assertEqual(Center.parents, [P1, P2])
        self.assertEqual(Center.siblings, [Sib])
        self.assertEqual(Center.half_siblings, [HS])
        self.assertEqual(Center.niblings, [Nib])
        self.assertEqual(Center.auncles, [A1, A2])
        self.assertEqual(Center.double_cousins, [DC])
        self.assertEqual(Center.cousins, [CO])
        self.assertEqual(Center.grandchildren, [GC])
        self.assertEqual(Center.grandparents, [GP1, GP2, GP3, GP4])
        self.assertEqual(Center.half_niblings, [HNib])
        self.assertEqual(Center.half_auncles, [HA])
        self.assertEqual(Center.great_grandchildren, [GGC])
        self.assertEqual(Center.great_grandparents, [GGP1, GGP2])
        self.assertEqual(Center.great_niblings, [GNib])
        self.assertEqual(Center.great_auncles, [GA])

        self.assertEqual(C.parents, [Center, Center_m])
        self.assertEqual(P1.children, [Sib, Center])
        self.assertEqual(P2.children, [Sib, Center, HS])
        self.assertEqual(DC.double_cousins, [Sib, Center])
        self.assertEqual(GNib.great_auncles, [Center])
        self.assertEqual(GNib.grandparents, [Sib, Sib_m])
        self.assertEqual(GA.great_niblings, [CO, Sib, Center, DC])
        self.assertEqual(HS.double_cousins, [])

if __name__ == '__main__':
    unittest.main()
    
