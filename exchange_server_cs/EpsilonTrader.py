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
    self.client = client

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
    self.V = V 

  def generateNextOrder(self):
    waitingTime = -(1/self.lmbda)*math.log(rand.random()/self.lmbda)
    priceEpsilon = 0.01
    buyOrSell = self.buyOrSell
    return waitingTime, priceEpsilon, buyOrSell

  def sendOrder(self, priceEpsilon, useless_variable):
    _shares = 5;
    if(self.buyOrSell == b'S'):
      print("\nSELL\n")
      _shares = 5 - exchange_factory1.SELL_COUNT
      price = self.V + priceEpsilon
    if(self.buyOrSell == b'B'):
      print("\nBUY\n")
      _shares = 5 - exchange_factory1.BUY_COUNT
      price = self.V - priceEpsilon

    order = OuchClientMessages.EnterOrder(
      order_token='{:014d}'.format(0).encode('ascii'),
      buy_sell_indicator=self.buyOrSell,
      shares=5,
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

