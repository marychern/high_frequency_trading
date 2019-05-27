from twisted.internet import reactor
import time

from clients_factory import ClientsFactory
from exchange_factory import ExchangeFactory
from underlying_value import UnderlyingValue
from message_handler import decodeServerOUCH, decodeClientOUCH


"""
Broker Class:
- only handles routing and timing functionalities
- this class wont need to know the details about the actual orders it handles
"""
class Broker():
	def __init__(self):
		self.initial_time = time.time()
		self.order_id = 0

		# orders[order_token] = client_id
		self.orders = {}

		self.clients = []
		self.exchange = None
		self.underlyingValueFeed = UnderlyingValue(self.time, self.clients)

	def data_recieved_from_exchange(self, data):
		#print(data)
		hello = None

	# returns the time elapsed from the start time (t = 0)
	def time(self):
		return time.time() - self.initial_time

	# assigns a unique order id / token and saves it with the requesting client
	# important so it can be returned
	def assign_order_token(self, client_id):
		order_token = '{:014d}'.format(self.order_id).encode('ascii')
		self.orders[order_token] = client_id
		self.order_id += 1
		return order_token

	def return_to_client(self, data):
		msg_type, msg = decodeServerOUCH(data) 
		client_id = self.orders[msg['order_token']]
		self.clients[client_id].transport.write(data)




def main():
	broker = Broker()

	reactor.listenTCP(8000, ClientsFactory(broker))
	reactor.connectTCP("localhost", 9001, ExchangeFactory(broker))

	reactor.callLater(60, reactor.stop)
	reactor.run()

if __name__ == '__main__':
	main()