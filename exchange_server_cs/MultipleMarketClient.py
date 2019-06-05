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
#- how tf do i do that,
##get the underlying values object of the two brokers for that stock and when it changes we will buy and sell
#should i init the two factories inside multiple market client?
#ok so clientfactory has custom protocols for each client and that makes sense
#
class MultipleMarketClient():
	def __init__(self):
		# self.client

		# initialize all the parameters for yaml
		parametersDict = self.getYaml()['parameters']
		keys = list(parametersDict.keys())
		self.V = None
		self.lmbda = parametersDict[keys[1]]
		self.mean = parametersDict[keys[2]]
		self.std = parametersDict[keys[3]]

		waitingTime, priceDelta, buyOrSell = self.generateNextOrder()
		reactor.callLater(waitingTime, self.sendOrder, priceDelta, buyOrSell)


	def getYaml(self):
		yml_path = 'external_clients.yaml'
		with open(yml_path, 'r') as f:
			try:
				configs = yaml.load(f)
			except yaml.YAMLError as e:
				raise e
		return configs



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
		self.trader  = MultipleMarketClient()

	def connectionMade(self):
		print("MultipleMarketClient has connected!")

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

#so the idea is that the custom client factory will hold the two connections and probably underlying value
#my protocol should hold my market client object and then it should do work from there
class MultipleMarketFactory(ClientFactory):
	protocol = MultipleMarket
	def __init__(self):
		super()
		self.marketOneConnection = None
		self.marketTwoConnection = None

	def buildProtocol(self, addr):
		print("inside buildProtocol!", file=sys.stderr)
		self.connection = ClientFactory.buildProtocol(self, addr)




def main():
	multipleMarketFactory = MultipleMarketFactory()
	multipleMarketFactory.protocol = MultipleMarket
	reactor.connectTCP('localhost', 8000, multipleMarketFactory)
	reactor.run()


if __name__ == '__main__':
	main()
	# reactor.connectTCP('localhost', 8000, multipleMarketFactory)
	# reactor.callLater(60, reactor.stop)
	# reactor.run()