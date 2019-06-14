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
    self.token = ['{:014d}'.format(0).encode('ascii'), '{:014d}'.format(1).encode('ascii')]
    #self.token = None
  
    # send a template order every second
    # note: have to use callLater, because of async issues
    # if first parameter is 0, wait 0 seconds to send order
    waitingTime, Epsilon = self.generateNextOrder()
    reactor.callLater(waitingTime, self.sendOrder, Epsilon)

    
  def generateNextOrder(self):
    Epsilon = 0.01    
    waitingTime = -(1/self.lmbda)*math.log(rand.random()/self.lmbda)
    return waitingTime, Epsilon


  # TODO: need to customize the information to send to exchange
  def sendOrder(self, Epsilon):
    token_idx = 0
    if(self.buy_or_sell != None):
      if(self.buy_or_sell == b'S'):
        print("\nSELL\n")
        token_idx = 1
        price = self.V + Epsilon
      if(self.buy_or_sell == b'B'):
        print("\nBUY\n")
        token_idx = 0
        price = self.V - Epsilon
      #self.token[token_idx] = '{:014d}'.format(token_idx).encode('ascii')
      #print("\nTOKEN: \n", self.token)
      order = OuchClientMessages.EnterOrder(
        order_token=self.token[token_idx],
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
    else:
      self.set_buy_or_sell()
    #remove if you dont want infinite loop
    waitingTime, Epsilon = self.generateNextOrder()
    #reactor.callLater(1, self.sendOrder)
    reactor.callLater(waitingTime, self.sendOrder, Epsilon)

  def set_underlying_value(self, V):
    if(self.V != V):
      self.cancel_all_orders()   
    self.V = V

  def handle_underlying_value(self, data):
    c, V = struct.unpack('cf', data)
    self.set_underlying_value(V)

  def cancel_all_orders(self):
    self.bid_count = 0
    self.ask_count = 0
    for i in self.token:
      order = OuchClientMessages.CancelOrder(
        order_token = i,
        shares = 1)

    self.token[0] = None
    self.token[1] = None
    self.client.transport.write(bytes(order))

  def set_buy_or_sell(self):
    if(self.ask_count > 5 and self.bid_count > 5): self.buy_or_sell = None
    elif(self.ask_count > 5 and self.bid_count <= 5): self.buy_or_sell = b'B'
    elif(self.ask_count <= 5 and self.bid_count > 5): self.buy_or_sell = b'S'
    else:
      if(self.buy_or_sell == None): self.buy_or_sell = b'B'

  def handle_accept_order(self, msg):
    if(str(msg).find("S") != -1):
      self.ask_count += 1
      self.set_buy_or_sell()
    elif(str(msg).find("B") != -1):
      self.bid_count += 1
      self.set_buy_or_sell()

  def handle_execute_or_cancel_order(self, msg):
    if(str(msg).find("S") != -1):
      self.buy_or_sell = b'S'
      self.ask_count -= 1
    elif(str(msg).find("B") != -1):
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
        if msg_type == b'A':
           print("Accepted Message from Exchange: ", msg)
           self.trader.handle_accept_order(msg)
        if msg_type == b'E':
           print("Executed Message from Exchange: ", msg)
           self.trader.handle_execute_or_cancel_order(msg)
        elif msg_type == b'C':
           print("Canceled Message from Exchange: ", msg)
           self.trader.handle_execute_or_cancel_order(msg)
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
