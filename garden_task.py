from garden import Garden
from numpy import floor
from tako import Tako, family_detection
from widget import *
import random
import numpy

class garden_task:
    last_action = None

    def __init__(self, environment, rand_percent, learning_on):
        self.env = environment
        self.rand_percent = rand_percent
        self.learning_on = learning_on
    
    def perform_action(self, action, tako):
        self.last_action = action
        tako.last_action = action
        result = self.env.perform_action(action, tako)
        tako.modify(result)

    def get_reward(self, tako):
        reward = 0
        full_diff = tako.fullness - tako.last_fullness
        bor_diff = tako.amuse - tako.last_amuse
        pain_diff = tako.pain - tako.last_pain
        if tako.pain != 0:
            if tako.last_pain == 0 and pain_diff == 0:
                pain_diff += 1
        desire_diff = tako.desire - tako.last_desire
        if full_diff > 0:
            reward += 1
        elif bor_diff > 0:
            reward += 1
        elif bor_diff < -0.5:
            reward += -1
        elif pain_diff > 0:
            reward += 1
        #if pain has increased
        if tako.pain > 0 and pain_diff >= 0:
            reward += -1
        #if desire has decreased more than its natural decay
        if desire_diff < -1.1:
            reward += 1
        return reward
    
    def find_action(self, action):
        highest = 0
        action = action[0]
        for i in range(len(action)):
            if action[highest] < action[i]:
                highest = i
        return highest

    def get_observation(self, tako):
        #drives are transformed to a sigmoid curve -2.5~2.5
        #this decision was the result of an experiment that showed it produced
        #better perfomance than not transforming it
        obs = self.env.get_sensors(tako)
        nobs = self.transform_obs(obs)
        full = 5/(1 + (0.38 * 2.71828)**(-tako.fullness + 75)) - 2.5
        nobs.append(full)
        amuse = 5/(1 + (0.38 * 2.71828)**(-tako.amuse + 75)) - 2.5
        nobs.append(amuse)
        pain = 5/(1 + (0.38 * 2.71828)**(-tako.pain + 75)) - 2.5
        nobs.append(pain)
        desire = 5/(1 + (0.38 * 2.71828)**(-tako.desire + 75)) - 2.5
        nobs.append(desire)
        #if tako is currently looking at another tako
        if nobs[4] == 1:
            #mateable?
            targ = self.env.get_target(tako)
            other_tako = self.env.garden_map[targ[1]][targ[0]]
            if other_tako.desire >= 100:
                nobs.append(1)
            else:
                nobs.append(-1)
            #find how related they are if need be
            if family_detection != None:
                nobs.append(tako.check_relations(other_tako))
            else:
                nobs.append(0)
        else:
            nobs.append(-1)
            nobs.append(0)
        return nobs
    
    def transform_obs(self, obs):
        normed = [0, 0, 0, 0, 0, 0]
        normed[obs] = 1
        return normed

    def interact_and_learn(self):
        #for each tako in env, get its observation
        for tako in self.env.tako_list:
            observation = self.get_observation(tako)
            #feed it the observation
            tako.solver.net.blobs['data'].data[...] = observation
            if self.learning_on:
                tako.solver.net.blobs['reward'].data[...] = 0
            tako.solver.net.blobs['stm_input'].data[...] = tako.last_action
            #forward and get action
            tako.solver.net.forward()
            act = tako.solver.net.blobs['action'].data
            action = self.find_action(act)
            #1/rand_percent chance of rolling different random action
            #(old experimental code)
            if self.rand_percent > 1:
                x = random.randint(0, self.rand_percent)
                if x == 0:
                    newact = random.randint(0, 5)
                    while newact == action:
                        newact = random.randint(0, 5)
                    action = newact
            #perform action and get reward
            self.perform_action(action, tako)
            if self.learning_on:
                reward = self.get_reward(tako)
                #feed it reward and backpropogate
                tako.solver.net.blobs['stm_input'].data[...] = -1
                for i in range(len(
                    tako.solver.net.blobs['reward'].data[0][0][0])):
                    feedback = reward + act[0][i]
                    tako.solver.net.blobs['reward'].data[0][0][0][i] = feedback
                tako.solver.step(1)
            
