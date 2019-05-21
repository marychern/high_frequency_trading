from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import reactor
from OuchServer.ouch_messages import OuchClientMessages
from random import randrange
import struct
import numpy as np
import random as rand
import math

import exchange_factory1 

class EpsilonTrader():

  def __init__(self, client, V = 100, lmbda=50, mean=0, std=0.2):
    self.order_type = "Enter"
    self.isVchanged = False
    self.shares = 1
    self.client = client
    self.first_run = True
    self.second_run = False
    self.V = V
    self.lmbda = lmbda
    self.mean = mean
    self.std = std
    self.buyOrSell = exchange_factory1.BUY_OR_SELL
    waitingTime, priceEpsilon, buyOrSell = self.generateNextOrder()
    reactor.callLater(waitingTime, self.sendOrder, priceEpsilon, buyOrSell)

  def set_buy_or_sell(self, buy_or_sell):
    self.buyOrSell = buy_or_sell

  def set_underlying_value(self, V): 
    if(self.V != V):
      self.isVchanged = True
      self.first_run = True
    self.V = V 

  def generateNextOrder(self):
    
    #if(self.isVchanged == True):
    #  #cancel all orders
      
   # if(self.first_run == True):
   #   self.first_run = False
   #   self.second_run = True
   #   self.buyOrSell = b'S'
   #   self.shares = 1000
   # elif(self.second_run == True):
   #   self.first_run = False
   #   self.second_run = False
   #   self.buyOrSell = b'B'
   #   self.shares = 1000
   # else:
   #   self.shares = 1000
    priceEpsilon = 0.01
    buyOrSell = self.buyOrSell

    waitingTime = -(1/self.lmbda)*math.log(rand.random()/self.lmbda)
    return waitingTime, priceEpsilon, buyOrSell

  def sendOrder(self, priceEpsilon, useless_variable):
    #_shares = 5;
    if(self.buyOrSell == b'S'):
      print("\nSELL\n")
     # _shares = 5 - exchange_factory1.SELL_COUNT
      price = self.V + priceEpsilon
    if(self.buyOrSell == b'B'):
      print("\nBUY\n")
      #_shares = 5 - exchange_factory1.BUY_COUNT
      price = self.V - priceEpsilon

    order = OuchClientMessages.EnterOrder(
      order_token='{:014d}'.format(0).encode('ascii'),
      buy_sell_indicator=self.buyOrSell,
      shares=self.shares,
      stock=b'AMAZGOOG',
      price=int(price * 10000),
      time_in_force=4,
      firm=b'OUCH',
      display=b'N',
      capacity=b'O',
      intermarket_sweep_eligibility=b'N',
      minimum_quantity=1,
      cross_type=b'N',
      customer_type=b' ')
    self.client.transport.write(bytes(order))

    waitingTime, priceEpsilon, self.buyOrSell = self.generateNextOrder()
    reactor.callLater(waitingTime, self.sendOrder, priceEpsilon, self.buyOrSell)

