from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import reactor
from OuchServer.ouch_messages import OuchClientMessages
from random import randrange
import struct
import numpy as np
import random as rand
import math
from message_handler import decodeServerOUCH, decodeClientOUCH

class Sniper():
	def __init__(self, client):
		self.V = 0
		self.marketConnect = None
		self.marketConnect2 = None
    self.buy_or_sell_market1 = b'B'
    self.buy_or_sell_market2 = b'S'
	  #how would it do the listening of V?
    #import the same underlying value object?
    #listen to the underlying value feed of broker and then have a function that whenever it changes we send a message to sniper

  def set_underlying_value(self, V):
    if(self.V != V):
      if(self.V > V): 
        self.buy_or_sell_market1 = b'B'
        self.buy_or_sell_market2 = b'S'
      else: #self.V < V
        self.buy_or_sell_market1 = b'S'
        self.buy_or_sell_market2 = b'B'
    self.V = V

  def handle_underlying_value(self, data):
    c, V = struct.unpack('cf', data)
    self.set_underlying_value(V)
  
  def sendOrder_Market1(self):
    self.tokens.append('{:014d}'.format(0).encode('ascii')) 
    order = OuchClientMessages.EnterOrder(
      order_token=self.tokens[self.token_idx],
      buy_sell_indicator=self.buy_or_sell_market1,
      shares=1,
      stock=b'AMAZGOOG',
      price=int(self.V * 10000),
      time_in_force=4,
      firm=b'OUCH',
      display=b'N',
      capacity=b'O',
      intermarket_sweep_eligibility=b'N',
      minimum_quantity=1,
      cross_type=b'N',
      customer_type=b' ')
    self.token_idx += 1
    self.client.transport.write(bytes(order))
    reactor.callLater(1, self.sendOrder_Market1)

  def sendOrder_Market2(self):
    self.tokens.append('{:014d}'.format(0).encode('ascii')) 
    order = OuchClientMessages.EnterOrder(
      order_token=self.tokens[self.token_idx],
      buy_sell_indicator=self.buy_or_sell_market2,
      shares=1,
      stock=b'AMAZGOOG',
      price=int(self.V * 10000),
      time_in_force=4,
      firm=b'OUCH',
      display=b'N',
      capacity=b'O',
      intermarket_sweep_eligibility=b'N',
      minimum_quantity=1,
      cross_type=b'N',
      customer_type=b' ')
    self.token_idx += 1
    self.client.transport.write(bytes(order))
    reactor.callLater(1, self.sendOrder_Market2)
  

class SniperClient(Protocol):
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
		self.trader = Sniper(self)


	def connectionMade(self):
		print('sniper has connected!')

	def dataReceived(self, data):

		ch = chr(data[0]).encode('ascii')
		header = chr(data[0])
		if (ch == b'@'):
			print("@ data:",data)
			# we only take the first 8 bytes because  unpack only takes 8 bytes only
			c, V = struct.unpack('cf', data[:8])
			print('V:',V)
			self.trader.set_underlying_value(V)
			#if there is more to unpack just call this function again
			if len(data)>8:
				# print("in more_messages, byte_length:",byte_length)
				self.dataReceived(data[8:])
		else:
			#handle the messages returned
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
			print("msg:",msg)
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

def main():
	sniperClientFactory = ClientFactory()
	sniperClientFactory.protocol = SniperClient
	reactor.connect("localhost", 8000, sniperClientFactory)
	reactor.callLater(120, reactor.stop)
	reactor.run()



if __name__ == '__main__':
	main()

