#~Bid_i(t) = BB_i - S * B(x(t), y(t))
#~Ask_i(t) = BO_i + S * A(x(t), y(t))


#Bid = min{[~Bid]s, BO - 2S}
#Ask = max{[~Ask]s, BB + 2S}



##
#create a robot  [X]

#connect to the proxy server []
# receive execute message and parse it [X]
# update robot's cash and inventory [X]
# Receive BA and BO []
# price = formulas above ^ [X]

# create messages []

# Send new message []
#

from __future__ import print_function

from twisted.internet import task
from twisted.internet.protocol import ClientFactory
from twisted.python import log
from twisted.internet.defer import Deferred

from sys import stdout
# import make_connection
from twisted.internet.protocol import Protocol
from twisted.internet import protocol

from twisted.words.protocols import irc

from make_connection import Greeter
from make_connection import gotProtocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages

#import make_connection
from make_connection import Greeter
from make_connection import gotProtocol

from twisted.protocols.basic import LineReceiver

#refer to master/hft/trader.py
from .utility import (MIN_BID, MAX_ASK)


aggressiveness = 0.5
b_x = 0.5 #slider 
b_y = 0.5 #slider 

a_x = 0.5 #slider 
a_y = 0.5 #slider 

x = 1 #get from broker 
y = 1 #get from broker


S_CONST = 1

#class Maker_Client(irc.IRCClient):
#class Maker_Client(Protocol):
class Maker(LineReceiver):

  def new_ask(self):
    ask_price = self.client.best_bid - S_CONST * aggressiveness
    self.client.ask_i = ask_price
    return ask_price

  def new_bid(self):
    bid_price = self.client.best_offer - S_CONST * aggressiveness
    self.client.bid_i = bid_price
    return bid_price

  def bid_aggressiveness(b_x, b_y, x, y):
    """
    B(x(t), y(t))
    x: order imbalance
    y: inventory position
    """
    return - b_x * x + b_y * y

  def sell_aggressiveness(a_x, a_y, x, y):
    """
    A(x(t), y(t))
    x: order imbalance
    y: inventory position
    """
    return a_x * x - a_y * y

  def latent_bid(bb, S, bid_aggressiveness):
    """
    LB(t)
    bb: best bid
    S: half a tick
    """
    return bb - S * bid_aggressiveness

  def latent_offer(bo, S, sell_aggressiveness):
    """
    LB(t)
    bb: best offer
    S: half a tick
    """
    return bo + S * sell_aggressiveness

  def start_algorithm(self):
    msg = "" 
    if self.best_bid > MIN_BID:
      msg = str(self.build_Message('B'))
    if self.best_offer < MAX_ASK:
      msg = str(self.build_Message('S'))
    return msg;

  def build_Message(self, Buy_or_Sell):
    if(Buy_or_Sell == 'S'):
      Price = self.new_ask() 
    else:
      Price = self.new_bid()

    #parameters: buy/sell and price
    message_type = OuchClientMessages.EnterOrder
    request = message_type (
      order_token='{:014d}'.format(1000).encode('ascii'), 
      buy_sell_indicator=Buy_or_Sell, shares=10, 
      stock=b'AMAZGOOG', 
      price=Price, 
      time_in_force=10000, 
      firm=b'OUCH',
      display=b'N', 
      capacity=b'O', 
      intermarket_sweep_eligibility=b'N', 
      minimum_quantity=1, 
      cross_type=b'N', 
      customer_type=b' '
    )
    return request

