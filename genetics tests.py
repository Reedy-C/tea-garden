import unittest
import tako
from textwrap import dedent
import os, sys
import caffe
sys.path.append('..')
from dgeann import dgeann

class testGenetics(unittest.TestCase):

    def setUp(self):
        self.data = dgeann.layer_gene(5, False, False, 0, "data",
                                        [], 9, "input")
        self.reward = dgeann.layer_gene(5, False, False, 0, "reward",
                                         [], 6, "input")
        self.stm_input = dgeann.layer_gene(5, False, False, 0, "stm_input",
                                             ["data", "reward"], 6, "input")
        self.stm = dgeann.layer_gene(5, False, False, 0, "STM",
                                       ["stm_input"], 6, "STMlayer")
        self.concat = dgeann.layer_gene(5, False, False, 0, "concat_0",
                                          ["data", "STM"], None, "concat")
        self.action = dgeann.layer_gene(5, False, False, 0, "action",
                                          ["concat_0"], 6, "IP")
        self.loss = dgeann.layer_gene(5, False, False, 0, "loss",
                                        ["action", "reward"], 5, "loss")

    def test_read(self):
        test_list  = {}
        concat_dict = {}
        test_list = self.data.read("testing alife.txt", test_list, concat_dict, None)
        test_list = self.reward.read("testing alife.txt", test_list, concat_dict, None)
        test_list = self.stm_input.read("testing alife.txt", test_list, concat_dict, None)
        test_list = self.stm.read("testing alife.txt", test_list, concat_dict, None)
        test_list = self.concat.read("testing alife.txt", test_list, concat_dict, None)
        test_list = self.action.read("testing alife.txt", test_list, concat_dict, None)
        test_list = self.loss.read("testing alife.txt", test_list, concat_dict, None)
        with open('testing alife.txt', 'r') as test_file:
            with open('alife.text', 'r') as orig_file:
                for line1, line2 in zip(test_file, orig_file):
                    self.assertEqual(line1, line2)
        os.remove("testing alife.txt")

    def test_default(self):
        #default genome; this needs to work!
        layers = [self.data, self.reward, self.stm_input, self.stm,
                  self.concat, self.action, self.loss]
        weights = []
        with open("default weights.txt") as f:
            for n in range(6):
                for m in range(15):
                    x = f.readline()
                    x = float(x[0:-1])
                    iden = str(n) + " " + str(m)
                    if m < 9:
                        in_layer = "data"
                        m_adj = m
                    else:
                        in_layer = "STM"
                        m_adj = m - 9
                    w = dgeann.weight_gene(5, False, False, 0, iden,
                                             x, m_adj, n, in_layer, "action")
                    weights.append(w)
        default_genome = dgeann.genome(layers, layers, weights, weights)
        test_default = caffe.Net('alife.text', 'test default genome.txt', caffe.TRAIN)
        default_tak_solv = default_genome.build()
        n = 0
        m = 0
        test_data = test_default.params['action'][0].data
        default_data = default_tak_solv.net.params['action'][0].data
        for n in range(6):
            for m in range(15):
                self.assertAlmostEqual(test_data[n][m], default_data[n][m])

    def test_mating(self):
        tak_1 = tako.Tako.default_tako(0, 0, 0, "Plain", False)
        tak_2 = tako.Tako.default_tako(0, 0, 1, "Plain", False)
        result = tak_1.mated(tak_2)
        self.assertEqual(result, ("boredom", -1))
        tak_1.desire = 150
        result = tak_1.mated(tak_2)
        self.assertEqual(result, ("boredom", -1))
        tak_1.desire = 0
        tak_2.desire = 150
        result = tak_1.mated(tak_2)
        self.assertEqual(result, ("boredom", -1))
        tak_1.desire = 100
        result = tak_1.mated(tak_2)
        self.assertEqual(len(result), 6)


if __name__ == '__main__':
    unittest.main()
    
