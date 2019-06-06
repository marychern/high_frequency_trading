from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import reactor
from OuchServer.ouch_messages import OuchClientMessages
from random import randrange
import struct
import numpy as np
import random as rand
import math
from message_handler import decodeServerOUCH, decodeClientOUCH

class Maker():
  def __init__(self, client, V=100, lmbda = 50):
		self.V = 0
    self.lmbda = lmbda
		self.marketConnect = None
	  self.marketConnect2 = None

  def set_underlying_value(self, V):
    self.V = V
 
  def handle_underlying_value(self, data):
    c, V = struct.unpack('cf', data)
    self.V = V
   
class MakerClient(Protocol):
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
		self.trader = Maker(self)


	def connectionMade(self):
		print('Maker has connected!')

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
	makerClientFactory = ClientFactory()
	makerClientFactory.protocol = MakerClient
	reactor.connect("localhost", 8000, makerClientFactory)
	reactor.callLater(120, reactor.stop)
	reactor.run()



if __name__ == '__main__':
	main()

