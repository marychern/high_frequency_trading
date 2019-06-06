from twisted.internet.protocol import ClientFactory, Protocol
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
import sys


##get connection from two running brokers

##get the underlying values object of the two brokers for that stock and when it changes we will buy and sell
#should i init the two factories inside multiple market client?
#ok so clientfactory has custom protocols for each client and that makes sense
#


#so the idea is that the custom client factory will hold the two connections and probably underlying value
#my protocol should hold my market client object and then it should do work from there
#this creates a protocol and client for each connection so i gotta call client factory in the
#client itself or protocol
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


		m = MultipleMarketFactory()
		m.protocol = MultipleMarket

		self.clientFactory = m
		self.protocol = m.protocol
		self.connectToBroker(self.clientFactory)


		print('clientFactory:{}'.format(self.clientFactory))
		print('protocol:{} '.format(self.protocol))

		waitingTime, priceDelta, buyOrSell = self.generateNextOrder()
		reactor.callLater(waitingTime, self.sendOrder, priceDelta, buyOrSell)






	def connectToBroker(self, factory):
		print('inside connectToBroker')
		reactor.connectTCP('localhost', 8000, factory)
		reactor.connectTCP('localhost', 8001, factory)
		# print('market factory in connecTobroker {}'.format(self.clientFactory))


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

	def sendOrder(self, priceDelta, buyOrSell):
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

		self.clientFactory.marketOneConnection.transport.write(bytes(order))


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
		print('initializing multiple market protocol!')



	# why tf does connectionmade not run?!!??!
	def connectionMade(self):
		print("-------------MultipleMarketClient has connected!------------")

	def dataReceived(self, data):
		# forward data to the trader, so they can handle it in different ways
		time.sleep(0.3)
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
	def __init__(self):
		super()
		self.marketOneConnection = None
		self.marketTwoConnection = None
		print('initialized factory!')

	def buildProtocol(self, addr):
		print("inside buildProtocol! addr:{}".format(addr))
		if self.marketOneConnection is None:
			self.marketOneConnection = ClientFactory.buildProtocol(self, addr)
			print('Inside buildprotocol, marketOneConnection:{}'.format(self.marketOneConnection))
		else:
			self.marketTwoConnection = ClientFactory.buildProtocol(self, addr)
			print('Inside buildprotocol, marketTwoConnection:{}'.format(self.marketTwoConnection))

	def getConnections(self):
		return self.marketOneConnection, self.marketTwoConnection





def main():
	m = MultipleMarketClient()
	reactor.run()



if __name__ == '__main__':
	main()
