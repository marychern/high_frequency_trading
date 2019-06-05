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
    self.ask_count = 0
    self.bid_count = 0
    self.tokens = []
    self.token_idx = 0
    self.num_shares = 1
    self.first_time = True

    # send a template order every second
    # note: have to use callLater, because of async issues
    # if first parameter is 0, wait 0 seconds to send order
    waitingTime, Epsilon, BuyOrSell = self.generateNextOrder()
    reactor.callLater(waitingTime ,self.sendOrder, Epsilon, BuyOrSell)

  def set_underlying_value(self, V):
    if(self.V != V):
      self.first_time = True
      #cancel all orders when v changes
      self.cancelAllOrders()
      self.first_move()
      
    self.V = V
    #cancel all orders when v changes
    
  def first_move(self):
    buy_sell = [b'B', b'S']
    for i in buy_sell:
      self.tokens.append('{:014d}'.format(0).encode('ascii'))
      message_price = int(self.V + 0.01 if(i == b'B') else self.V-0.01)
      message_type = OuchClientMessages.EnterOrder
      order = message_type(
        order_token=self.tokens[self.token_idx],
        buy_sell_indicator=i,
        shares=5,
        stock=b'AMAZGOOG',
        price= message_price,
        time_in_force=4,
        firm=b'OUCH',
        display=b'N',
        capacity=b'O',
        intermarket_sweep_eligibility=b'N',
        minimum_quantity=1,
        cross_type=b'N',
        customer_type=b' ')
      self.token_idx = self.token_idx + 1
      print('-----------ORDER is:{}-------------------'.format(order))
      self.client.transport.write(bytes(order))
    

  def generateNextOrder(self):
    Epsilon = 0.01    
    waitingTime = -(1/self.lmbda)*math.log(rand.random()/self.lmbda)
    return waitingTime, Epsilon, self.buy_or_sell

  def cancelAllOrders(self):
    for i in self.tokens:
      order = OuchClientMessages.CancelOrder(
        order_token = i,
        shares = 1)
      self.tokens.remove(i)
      self.token_idx = 0
      self.client.transport.write(bytes(order))

  # TODO: need to customize the information to send to exchange
  def sendOrder(self, Epsilon, variable):
    if(self.buy_or_sell != None):
      if(self.buy_or_sell == b'S'):
        print("\nSELL\n")
        price = self.V + Epsilon
      if(self.buy_or_sell == b'B'):
        print("\nBUY\n")
        price = self.V - Epsilon
      self.tokens.append('{:014d}'.format(0).encode('ascii')) 
      order = OuchClientMessages.EnterOrder(
        order_token=self.tokens[self.token_idx],
        buy_sell_indicator=self.buy_or_sell,
        shares=self.num_shares,
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
      self.token_idx = self.token_idx + 1
      self.client.transport.write(bytes(order))
      #remove if you dont want infinite loop
      waitingTime, Epsilon, self.buy_or_sell = self.generateNextOrder()
      #reactor.callLater(1, self.sendOrder)
      reactor.callLater(waitingTime, self.sendOrder, Epsilon, self.buy_or_sell)

  def handle_underlying_value(self, data):
    c, V = struct.unpack('cf', data)
    self.V = V
    #print("Underlying Value Change: ", V)

  def handle_executed_order(self, msg):
    print("Executed Message from Exchange: ", msg)
    # TODO: if order executed... do something
    if(str(msg).find("S") != -1):
      print("\nExecute: ask found\n")
      self.ask_count -= 1
      self.buy_or_sell = b'S'
    elif(str(msg).find("B") != -1):
      print("\nExecute: bid found\n")
      self.buy_or_sell = b'B'
      self.bid_count -= 1
  
  def handle_cancelled_order(self, msg):
    print("Cancelled Message: ", msg)
    # TODO: if order cancelled... do something
    if(str(msg).find("S") != -1):
      print("\nCancel: ask found\n")
      self.ask_count -= 1
      self.buy_or_sell = b'S'
    elif(str(msg).find("B") != -1):
      print("\nCancel: bid found\n")
      self.buy_or_sell = b'B'
      self.bid_count -= 1
    

class ExternalClient(Protocol):
  bytes_needed = {
    'B': 10,
    'S': 10,
    'E': 40,
    'C': 28,
    'U': 80,
    'A': 66,
    'Q': 33,
  }

  def __init__(self, trader_class):
    self.trader = trader_class(self)

  def connectionMade(self):
    print("client connected")

  def dataReceived(self, data):

    print("\nInside dataReceived:\n ", data)
    # forward data to the trader, so they can handle it in different ways
    ch = chr(data[0]).encode('ascii')
    header = chr(data[0])
    # best bid best offer feed

    if (ch == b'@'):
      print("@ data:", data)
      # we only take the first 8 bytes because  unpack only takes 8 bytes only
      c, V = struct.unpack('cf', data[:8])
      print('V:', V)
      self.trader.set_underlying_value(V)
      # if there is more to unpack just call this function again
      if len(data) > 8:
        # print("in more_messages, byte_length:",byte_length)
        self.dataReceived(data[8:])
    else:
        try:
          bytes_needed =  self.bytes_needed[header]
        except KeyError:
          print("Key error data: {}".format(data))
          raise ValueError('unknown header %s.' % header)

        if len(data) >= bytes_needed:
            remainder = bytes_needed
            more_data = data[remainder:]
            data = data[:bytes_needed]
        msg_type, msg = decodeServerOUCH(data)
        print("\nMESSAGE:\n ", msg)
        if msg_type == b'E':
           self.trader.handle_executed_order(msg)
        elif msg_type == b'C':
           self.trader.handle_cancelled_order(msg)
        else:
           print("unhandled message type: ", data)
        if len(more_data):
            self.dataReceived(more_data)

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
