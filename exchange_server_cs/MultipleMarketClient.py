from twisted.internet.protocol import ClientFactory, Protocol, ServerFactory, Factory
from twisted.internet import reactor
from OuchServer.ouch_messages import OuchClientMessages
from random import randrange
import struct
import numpy as np
import random as rand
import math
import time
from message_handler import decodeServerOUCH, decodeClientOUCH
import yaml

counter = 0



#so i have to pass broker into
class MultipleMarketClient:
	def __init__(self):
		# self.client
		print('initialized client!')
		# initialize all the parameters for yaml
		parametersDict = self.getYaml()['parameters']
		keys = list(parametersDict.keys())
		self.V = parametersDict[keys[0]]
		self.lmbda = parametersDict[keys[1]]
		self.mean = parametersDict[keys[2]]
		self.std = parametersDict[keys[3]]
		self.protocolOne = None
		self.protocolTwo = None



	def set_underlying_value(self, V):
		self.V = V


	def generateNextOrder(self):
		waitingTime = -(1 / self.lmbda) * math.log(rand.random() / self.lmbda)
		priceDelta = np.random.normal(self.mean, self.std)
		randomSeed = rand.random()

		if (randomSeed > .5):
			buyOrSell = b'B'
		else:
			buyOrSell = b'S'
		return waitingTime, priceDelta, buyOrSell

	def getYaml(self):
		yml_path = 'external_clients.yaml'
		with open(yml_path, 'r') as f:
			try:
				configs = yaml.load(f)
			except yaml.YAMLError as e:
				raise e
		return configs

	def sendOrder(self, priceDelta, buyOrSell, id):
		print('Protocol:{} is sending and Order!'.format(id))
		price = self.V + priceDelta
		order = OuchClientMessages.EnterOrder(
			order_token='{:014d}'.format(0).encode('ascii'),
			buy_sell_indicator=buyOrSell,
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
		if id == 1:
			self.protocolOne.transport.write(bytes(order))
		else:
			self.protocolTwo.transport.write(bytes(order))
		waitingTime, priceDelta, buyOrSell = self.generateNextOrder()
		reactor.callLater(waitingTime, self.sendOrder, priceDelta, buyOrSell, id)


	def handle_underlying_value(self, data):
		c, V = struct.unpack('cf', data)
		self.set_underlying_value(V)

	def handle_accepted_order(self, msg):
		print("Accept Message from Exchange: ", msg)

	def handle_executed_order(self, msg):
		print("Executed Message from Exchange: ", msg)

	def handle_cancelled_order(self, msg):
		print("Cancelled Message: ", msg)

class MultipleMarket(Protocol):
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
		print('initializing multiple market protocol!')
		self.trader = None
		counter += 1
		self.id = counter
		print('id initialized to:{}'.format(self.id))

	# why tf does connectionmade not run?!!??!
	def connectionMade(self):
		print("-------------MultipleMarketClient has connected!------------")
		self.trader = self.factory.trader
		print('In protocol init: Trader is  {}'.format(self.trader))
		if self.id == 1:
			self.trader.protocolOne = self
		elif self.id == 2:
			self.trader.protocolTwo = self
		wTime, pDelta, buySell = self.trader.generateNextOrder()
		self.trader.sendOrder(pDelta, buySell, self.id)

	def dataReceived(self, data):
		# time.sleep(0.3)
		print('id:{}'.format(self.id))
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


class MultipleMarketFactory(ClientFactory):
	protocol = MultipleMarket
	def __init__(self, trader):
		self.trader = trader
		print('initialized factory!')



def main():
	multipleTrader = MultipleMarketClient()
	print('Trader is  {}'.format(multipleTrader))
	reactor.connectTCP("localhost", 8000, MultipleMarketFactory(multipleTrader))
	reactor.connectTCP("localhost", 8001, MultipleMarketFactory(multipleTrader))
	reactor.run()



if __name__ == '__main__':
	main()
