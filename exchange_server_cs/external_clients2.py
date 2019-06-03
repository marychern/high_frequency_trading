from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import reactor
from OuchServer.ouch_messages import OuchClientMessages
from random import randrange
import struct
import numpy as np
import random as rand
import math
from message_handler import decodeServerOUCH, decodeClientOUCH
#Traders
import RandomTrader
import MakerTrader
import time

class ExternalClient(Protocol):
  def __init__(self):
    #specify trader
    #self.trader = MakerTrader.MakerTrader(self)
    self.trader = RandomTrader.RandomTrader(self)

  def connectionMade(self):
    print("client connected")

  def dataReceived(self, data):
      # forward data to the trader, so they can handle it in different ways
      time.sleep(0.3)
      ch = chr(data[0]).encode('ascii')
      header = chr(data[0])
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
          # handle the messages returned
          try:
              bytes_needed = self.bytes_needed[header]
          except KeyError:
              print("Key error data: {}".format(data))
              raise ValueError('unknown header %s.' % header)

          if len(data) >= bytes_needed:
              remainder = bytes_needed
              more_data = data[remainder:]
              data = data[:bytes_needed]
          msg_type, msg = decodeServerOUCH(data)
          print("msg:", msg)
          if msg_type == b'A':
              self.trader.handle_accepted_order(msg)
          elif msg_type == b'E':
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
    externalClientFactory.protocol = ExternalClient
    reactor.connectTCP("localhost", 8002, externalClientFactory)
    reactor.run()

if __name__ == '__main__':
    main()
