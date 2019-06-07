from twisted.internet.protocol import ClientFactory, Protocol, ServerFactory, Factory
from twisted.internet import reactor
from OuchServer.ouch_messages import OuchClientMessages
from random import randrange
import struct
import numpy as np
import random as rand
import math
from message_handler import decodeServerOUCH, decodeClientOUCH
import yaml
from inventory import Inventory
#spread is BB - BO
#need to get the BB and BO
# from extracting the Q message

#need to add order token to inventory's token list whenever we send another order
#need to add it to actual inventory when receiving an executed message
#need to sell that order to chicago after receiving from new york.

counter = -1

exchanges = ['NEW YORK', 'CHICAGO']

class Maker:
  def __init__(self):
    print('Initialized Maker!')

    # initialize all the parameters for yaml
    parametersDict = self.getYaml()['parameters']
    keys = list(parametersDict.keys())
    self.V = parametersDict[keys[0]]
    self.lmbda = parametersDict[keys[1]]
    self.mean = parametersDict[keys[2]]
    self.std = parametersDict[keys[3]]
    
    self.protocolOne = None
    self.protocolTwo = None
    self.spread = 0
    self.inventory_count = 0
    self.inventory = Inventory(100000)

  def set_underlying_value(self, V):
    self.V = V


  def generateNextOrder(self):
    waitingTime = -(1 / self.lmbda) * math.log(rand.random() / self.lmbda)
    randomSeed = rand.random()

    if randomSeed > .5:
      buyOrSell = b'B'
    else:
      buyOrSell = b'S'
    return waitingTime, buyOrSell

  def getYaml(self):
    yml_path = 'external_clients.yaml'
    with open(yml_path, 'r') as f:
      try:
        configs = yaml.load(f)
      except yaml.YAMLError as e:
        raise e
    return configs

  def calcSpread(self, msg):
    bestBid = msg['best_bid']
    bestOffer = msg['best_ask']
    print('BestBid:{} BestOffer:[}'.format(bestBid, bestOffer))
    self.spread = bestBid - bestOffer
    print('Spread:{}'.format(self.spread))

  def sendOrder(self, buyOrSell, id):
    print('Sending an order to {}'.format(exchanges[id]))

    price = (self.V + self.spread)/2
    if(buyOrSell == b'B'):
      price = (self.V + self.spread)/2
    else:
      price = (self.V - self.spread)/2
      
    order_token = '{:014d}'.format(0).encode('ascii')
    order = OuchClientMessages.EnterOrder(
      order_token=order_token,
      buy_sell_indicator = buyOrSell,
      shares=1,
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
    print('---------------ORDER is:{}--------------'.format(order))
    if id == 0:
      self.protocolOne.transport.write(bytes(order))
      waitingTime, buyOrSell = self.generateNextOrder()
      reactor.callLater(waitingTime, self.sendOrder, buyOrSell, id)
    else:
      self.protocolTwo.transport.write(bytes(order))
      print('Sent a message to {}!'.format(exchanges[id]))

  def handle_underlying_value(self, data):
    c, V = struct.unpack('cf', data)
    self.set_underlying_value(V)

  def handle_accepted_order(self, msg, id):
    print("Accept Message from {}: {}".format(exchanges[id], msg))

  def handle_executed_order(self, msg, id):
    print("Executed Message from {}: {}".format(exchanges[id], msg))
    if(str(msg).find("B") != -1):
      self.inventory_count += 1
    elif(str(msg).find("S") != -1):
      self.inventory_count -= 1
    if(self.inventory_count > 0):
      self.sendOrder(self, b'S', 1)
    else:
      self.sendOrder(self, b'B', 0)

  def handle_cancelled_order(self, msg, id):
    print("Cancelled Message from {}: {}".format(exchanges[id], msg))


class MakerProtocol(Protocol):
  bytes_needed = {
    'B': 10,
    'S': 10,
    'E': 40,
    'C': 28,
    'U': 80,
    'A': 66,
    'Q': 33,
  }
  def __init__(self):
    global counter
    self.trader = None
    counter += 1
    self.id = counter
    print('Initialized Maker Protocol! id:{}'.format(self.id))


  def connectionMade(self):
    print('--------------Maker Protocol has connected--------------')
    self.trader = self.factory.trader
    if self.id == 0:
      self.trader.protocolOne = self
    elif self.id == 1:
      self.trader.protocolTwo = self
    if self.id == 0:
      wTime, pDelta, buySell = self.trader.generateNextOrder()
      self.trader.sendOrder(buySell, self.id)


  def dataReceived(self, data):
    print('Received info from {} exchange'.format(exchanges[self.id]))
    ch = chr(data[0]).encode('ascii')
    header = chr(data[0])
    # check if broker sent back an underlying value change back
    if ch == b'@':
      if self.id == 0:
        print("@ data:",data)
        # we only take the first 8 bytes because  unpack only takes 8 bytes only
        c, V = struct.unpack('cf', data[:8])
        print('V:',V)
        if self.trader.V != V:
          print('Underlying Value Changed!')
          self.trader.sendOrder(b'S', 0)
          self.trader.sendOrder(b'B', 0)
        self.trader.set_underlying_value(V)
      #if there is more to unpack or decode just call this function again
      if len(data)>8:
        self.dataReceived(data[8:])
    else:
      #handles the message type being returned
      try:
        bytes_needed = self.bytes_needed[header]
      except KeyError:
        print("Key error data: {}".format(data))
        raise ValueError('unknown header %s.' % header)
      #splits the data received into bytes based on the header
      #the remainder of the data is to be handled recursively
      #We need to do this because some times the exchange sends huge chunks
      #of data in the byte stream and our decoder needs the data in identifiable chunks
      if len(data) >= bytes_needed:
        remainder = bytes_needed
        more_data = data[remainder:]
        data = data[:bytes_needed]

      msg_type, msg = decodeServerOUCH(data)
      print("msg:",msg)
      if msg_type == b'A':
        self.trader.handle_accepted_order(msg, self.id)
      elif msg_type == b'E':
        self.trader.handle_executed_order(msg, self.id)
      elif msg_type == b'C':
        self.trader.handle_cancelled_order(msg, self.id)
      elif msg_type == b'Q': # this is the BB/BO message
        self.trader.calcSpread(msg)
      else:
        print("unhandled message type: ", data)
      if len(more_data):
        self.dataReceived(more_data)


class MakerFactory(ClientFactory):
  protocol = MakerProtocol
  def __init__(self, trader):
    self.trader = trader
    print('Initialized factory!')

def main():
  maker = Maker()
  reactor.connectTCP("localhost", 8000, MakerFactory(maker))
  reactor.connectTCP("localhost", 8001, MakerFactory(maker))
  reactor.run()


if __name__ == '__main__':
  main()
