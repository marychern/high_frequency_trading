from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ServerFactory, ClientFactory
import random as rand
import numpy as np
import math
import matplotlib.pyplot as plt
from struct import *
from message_handler import decodeServerOUCH, decodeClientOUCH
import time
import csv
import pickle
import yaml
import sys
"""
===== Underlying Value Feed =====

This is the underlying V, that will control where the traders tend
to submit orders. When the state of the underlying value changes,
all traders will be notified.

Note: All underlying value broadcasts will start with: @

==================================
"""

class UnderlyingValue():
    def __init__(self, time, clients):
        rand.seed(3)
        np.random.seed(4)
        # keep track of subscribers
        self.time = time
        self.clients = clients

        # initialize constants for random number generators
        #self.T = 0

        #initialize all the parameters for yaml
        parametersDict = self.getYaml()['parameters']
        keys = list(parametersDict.keys())
        self.V = parametersDict[keys[0]]
        self.lmbda = parametersDict[keys[1]]
        self.mean = parametersDict[keys[2]]
        self.std = parametersDict[keys[3]]

        # initialize graph for data visualization
        self.timeAxis = []
        self.valueAxis = []
        self.timeAxis.append(0)
        self.valueAxis.append(parametersDict[keys[0]])

        self.broadcast()

        # schedule the first price jump (uses poisson process)
        waitingTime, jumpHeight = self.generateNextJump()
        reactor.callLater(waitingTime, self.jump, waitingTime, jumpHeight)

    # controls the waiting time and the height of the next jump
    def jump(self, waitingTime, jumpHeight):
        self.V += jumpHeight
        self.broadcast()
        time = self.time()

        # store values for data visualization
        self.timeAxis.append(time)
        self.valueAxis.append(self.V)

        waitingTime, jumpHeight = self.generateNextJump()
        reactor.callLater(waitingTime, self.jump, waitingTime, jumpHeight)

    # send message out to all clients
    def broadcast(self):
        msg = "@" + str(self.V)
        for client in self.clients:
            m = pack('cf', b'@', self.V)
            client.transport.write(bytes(m))

    # implements the poisson process and normal distribution
    def generateNextJump(self):
        waitingTime = -(1/self.lmbda)*math.log(rand.random()/self.lmbda)
        jumpHeight = np.random.normal(self.mean, self.std)
        return (waitingTime, jumpHeight)

    # called after the factory ends
    def graph_results(self, end_time):
        self.timeAxis.append(end_time)
        plt.hlines(self.valueAxis[:-1], self.timeAxis[:-2], self.timeAxis[1:], linewidth=1, label="Fundamental Value")
        plt.vlines(self.timeAxis[1:-1], self.valueAxis, self.valueAxis[1:], linewidth=1)

        pickle.dump(self.timeAxis, open("timeAxis.pickle", "wb"))
        pickle.dump(self.valueAxis, open("valueAxix.pickle", "wb"))

        # dump to csv file
        with open('data_points.csv', mode='a') as data_file:
            data_writer = csv.writer(data_file, delimiter='\n', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            data_writer.writerow(["UNDERLYING VALUES"])
            data_writer.writerow(self.valueAxis)
        data_file.close()

    #returns the structure of the yaml file
    #look at  https://github.com/marychern/high_frequency_trading/blob/yaml/exchange_server_116/yamlExample.py
    #for more info
    def getYaml(self):
        yml_path = 'broker.yaml'
        with open(yml_path, 'r') as f:
            try:
                configs = yaml.load(f)
            except yaml.YAMLError as e:
                raise e
        return configs
