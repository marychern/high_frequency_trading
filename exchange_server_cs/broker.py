from twisted.internet import reactor
import time

from clients_factory import ClientsFactory
from exchange_factory import ExchangeFactory
from underlying_value import UnderlyingValue

#configure broker
#isMultipleMarkets = True
Market1Port = 9001
#Market2Port = 9002


"""
Broker Class:
- only handles routing and timing functionalities
- this class wont need to know the details about the actual orders it handles
"""
class Broker():
  def __init__(self):
    self.initial_time = time.time()
    self.order_id = 0
    self.orders = {}

    self.clients = []
    self.exchange = None
    self.underlyingValueFeed = UnderlyingValue(self.time, self.clients)

  def data_recieved_from_exchange(self, data):
    print("\ndata_recieved inside broker: \n",data)
    hello = None

  def time(self):
    return time.time() - self.initial_time

  def get_order_token(self, client_id):
    order_token = '{:014d}'.format(self.order_id).encode('ascii')
    self.orders[order_token] = client_id
    self.order_id += 1
    return order_token

def main():
  broker = Broker()
  reactor.listenTCP(8000, ClientsFactory(broker))
  reactor.connectTCP("localhost", Market1Port, ExchangeFactory(broker))
#  if(isMultipleMarkets):
#    reactor.listenTCP(8001, ClientsFactory(broker))
#    reactor.connectTCP("localhost", Market2Port, ExchangeFactory(broker))

  reactor.callLater(120, reactor.stop)
  reactor.run()

if __name__ == '__main__':
  main()
