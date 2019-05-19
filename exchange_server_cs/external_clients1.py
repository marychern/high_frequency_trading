from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import reactor
from OuchServer.ouch_messages import OuchClientMessages
from random import randrange
import struct
import numpy as np
import random as rand
import math

#Traders
import RandomTrader
import MakerTrader
import EpsilonTrader

class ExternalClient(Protocol):
  def __init__(self):
    #specify trader
    #self.trader = MakerTrader.MakerTrader(self)
    #self.trader = RandomTrader.RandomTrader(self)
    self.trader = EpsilonTrader.EpsilonTrader(self)

  def connectionMade(self):
    print("client connected")

  def dataReceived(self, data):
    # forward data to the trader, so they can handle it in different ways
    print("\nDATA FROM EXTERNAL CLIENT: \n", data)
    ch = chr(data[0]).encode('ascii')
    #buyOrSell = chr(data[17]).encode('ascii')
    
    if (ch == b'@'):
      c, V = struct.unpack('cf', data)
      self.trader.set_underlying_value(V)
    #if (data == b'B')
    else:
      print("unhandled message type")

# -----------------------
# Main function
# -----------------------
def main():
    externalClientFactory = ClientFactory()
    externalClientFactory.protocol = ExternalClient
    reactor.connectTCP("localhost", 8001, externalClientFactory)
    reactor.run()

if __name__ == '__main__':
    main()
