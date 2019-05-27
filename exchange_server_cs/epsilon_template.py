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

class RandomTrader():
	def __init__(self, client):
		rand.seed(1)
		np.random.seed(2)
		self.client = client

		# send a template order every second
		# note: have to use callLater, because of async issues
		
		reactor.callLater(1, self.sendOrder)


	def sendOrder(self):
		order = OuchClientMessages.EnterOrder(
			order_token='{:014d}'.format(0).encode('ascii'),
			buy_sell_indicator=b'B',
			shares=1,
			stock=b'AMAZGOOG',
			price=10,
			time_in_force=4,
			firm=b'OUCH',
			display=b'N',
			capacity=b'O',
			intermarket_sweep_eligibility=b'N',
			minimum_quantity=1,
			cross_type=b'N',
			customer_type=b' ')
		self.client.transport.write(bytes(order))

		reactor.callLater(1, self.sendOrder)


	def handle_underlying_value(self, data):
		c, V = struct.unpack('cf', data)
		#print("Underlying Value Change: ", V)

	def handle_accepted_order(self, msg):
		print("Accept Message from Exchange: ", msg)

	def handle_executed_order(self, msg):
		print("Executed Message from Exchange: ", msg)

	def handle_cancelled_order(self, msg):
		print("Cancelled Message: ", msg)

class ExternalClient(Protocol):
	def __init__(self, trader_class):
		self.trader = trader_class(self)

	def connectionMade(self):
		print("client connected")

	def dataReceived(self, data):
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
		return ExternalClient(RandomTrader)
	externalClientFactory.protocol = externalClient
	reactor.connectTCP("localhost", 8000, externalClientFactory)
	reactor.run()

if __name__ == '__main__':
    main()
