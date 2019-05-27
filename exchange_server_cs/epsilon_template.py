from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import reactor
from OuchServer.ouch_messages import OuchClientMessages
from random import randrange
import struct
import numpy as np
import random as rand
import math
from message_handler import decodeServerOUCH, decodeClientOUCH

"""
Note on assumption:
The OUCH message expects price to be an integer. We think this means
if we want $100.30, this is represented as 10030
"""

class EpsilonTrader():
  def __init__(self, client, V=100, lmbda = 50):
    rand.seed(1)
    np.random.seed(2)
    self.client = client
    self.V = V
    self.lmbda = lmbda
    self.buy_or_sell = b'B'
    self.sell_count = 0
    self.buy_count = 0
    # send a template order every second
    # note: have to use callLater, because of async issues
    # if first parameter is 0, wait 0 seconds to send order
    waitingTime, Epsilon, BuyOrSell = self.generateNextOrder()
    reactor.callLater(waitingTime ,self.sendOrder, Epsilon, BuyOrSell)

  def set_buy_or_sell(self, buy_or_sell):
    self.buy_or_sell = buy_or_sell

  def set_underlying_value(self, V):
    self.V = V

  def generateNextOrder(self):
    Epsilon = 0.01    
    waitingTime = -(1/self.lmbda)*math.log(rand.random()/self.lmbda)
    return waitingTime, Epsilon, self.buy_or_sell

  # TODO: need to customize the information to send to exchange
  def sendOrder(self, Epsilon, variable):
    if(self.buy_or_sell == b'S'):
      print("\nSELL\n")
      price = self.V + Epsilon
    if(self.buy_or_sell == b'B'):
      print("\nBUY\n")
      price = self.V - Epsilon

    order = OuchClientMessages.EnterOrder(
      order_token='{:014d}'.format(0).encode('ascii'),
      buy_sell_indicator=self.buy_or_sell,
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
    self.client.transport.write(bytes(order))
    # remove if you dont want infinite loop
    # reactor.callLater(1, self.sendOrder)
    waitingTime, Epsilon, self.buy_or_sell = self.generateNextOrder()
    reactor.callLater(waitingTime, self.sendOrder, Epsilon, self.buy_or_sell)

  def handle_underlying_value(self, data):
    c, V = struct.unpack('cf', data)
    self.V = V
    #print("Underlying Value Change: ", V)

  def handle_accepted_order(self, msg):
    print("Accept Message from Exchange: ", msg)
    # TODO: if order accepted... do something
    if(msg.find("ask")):
      self.sell_count += 1
      if(self.sell_count >= 5 and self.buy_count < 5): self.buy_or_sell = b'B'
    elif(msg.find("bid")):
      self.buy_count += 1
      if(self.buy_count >= 5 and self.sell_count < 5): self.buy_or_sell = b'B'

  def handle_executed_order(self, msg):
    print("Executed Message from Exchange: ", msg)
    # TODO: if order executed... do something
    if(msg.find("ask")):
      self.sell_count -= 1
      self.buy_or_sell = b'S'
    elif(msg.find("bid")):
      self.buy_or_sell = b'B'
      self.buy_count -= 1
  
  def handle_cancelled_order(self, msg):
    print("Cancelled Message: ", msg)
    # TODO: if order cancelled... do something
    if(msg.find("ask")):
      self.sell_count -= 1
      self.buy_or_sell = b'S'
    elif(msg.find("bid")):
      self.buy_or_sell = b'B'
      self.buy_count -= 1
    


class ExternalClient(Protocol):
  def __init__(self, trader_class):
    self.trader = trader_class(self)

  def connectionMade(self):
    print("client connected")

  def dataReceived(self, data):
    print("\nInside dataReceived:\n ", data)
    # forward data to the trader, so they can handle it in different ways
    ch = chr(data[0]).encode('ascii')
    
    # best bid best offer feed
    if (ch == b'@'):
      self.trader.handle_underlying_value(data)
    else:
      msg_type, msg = decodeServerOUCH(data) 
      if msg_type == b'A':
        self.trader.handle_accepted_order(msg)
      elif msg_type == b'E':
        self.trader.handle_executed_order(msg)
      elif msg_type == b'C':
        self.trader.handle_cancelled_order(msg)
      else:
        print("unhandled message type: ", data)

# -----------------------
# Main function
# -----------------------
def main():
  externalClientFactory = ClientFactory()
  def externalClient():
    return ExternalClient(EpsilonTrader)
  externalClientFactory.protocol = externalClient
  reactor.connectTCP("localhost", 8000, externalClientFactory)
  reactor.run()

if __name__ == '__main__':
    main()
