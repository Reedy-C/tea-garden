import unittest
import csv
import tako
import sys
sys.path.append('..')
from dgeann import dgeann

class testGenetics(unittest.TestCase):

    def setUp(self):
        tako.random.seed("genetics")
        self.fields = ['dom', 'can_mut', 'can_dup', 'mut_rate', 'ident',
                      'weight', 'in_node', 'out_node', 'in_layer', 'out_layer']

    #'plain' diploid
    def test_p_diploid(self):
        tak = tako.Tako.default_tako(0, True, 0, 0, "Plain", False)
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
        tak = tako.Tako.default_tako(0, True, 0, 0, "Diverse", False)
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
        tak = tako.Tako.default_tako(0, True, 0, 0, "Haploid", False)
        with open("Default Genetics/15_a.csv") as file:
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
        tak = tako.Tako.default_tako(0, True, 0, 0, "Haploid", True)
        for i in range(len(tak.genome.weightchr_a)):
            self.assertEqual(tak.genome.weightchr_a[i].weight,
                             tak.genome.weightchr_b[i].weight)

    def test_mating(self):
        tak_1 = tako.Tako.default_tako(0, True, 0, 0, "Plain", False)
        tak_2 = tako.Tako.default_tako(0, True, 0, 1, "Plain", False)
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
        self.assertEqual(len(result), 6)
        self.assertEqual(tak_1.desire, 0)
        self.assertEqual(tak_2.desire, 0)
        self.assertEqual(tak_1.dez, 0)
        self.assertEqual(tak_2.dez, 0)
        tak_1.update()
        tak_2.update()
        self.assertAlmostEqual(tak_1.desire, 0.01, places=2)
        self.assertAlmostEqual(tak_2.desire, 0.01, places=2)
        self.assertEqual(tak_1.dez, 1)
        self.assertEqual(tak_2.dez, 1)

if __name__ == '__main__':
    unittest.main()
    
