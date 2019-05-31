from twisted.internet.protocol import Protocol, ClientFactory
from message_handler import decodeServerOUCH
import matplotlib.pyplot as plt
import time
from collections import OrderedDict 
import numpy as np
import pickle
from message_handler import decodeServerOUCH, decodeClientOUCH

cda_crossTime = pickle.load(open("output/cda_crossTime.pickle", "rb"))

class Exchange(Protocol):
  def connectionMade(self):
    self.factory.broker.exchange = self
    print("exchange connected")

  def dataReceived(self, data):
    try:
      msg_type, msg = decodeServerOUCH(data) 
      if msg_type == b'A':
        #print('accepted: ', msg)
        self.factory.broker.return_to_client(data)
        self.factory.graph.plot_accepted_order(msg)

      elif msg_type == b'E':
        #print('executed: ', msg)
        self.factory.broker.return_to_client(data)
        self.factory.graph.plot_executed_order(msg)

      # currently ignores cancelled, because these are 
      # just orders that ran out of time and no one matched
      elif msg_type == b'C':
        #print('cancelled: ', msg)
        #self.factory.graph.plot_cancelled_order(msg)
        self.factory.broker.return_to_client(data)
        hello = 0

      elif msg_type == b'Q':
        #print('BBBO: ', msg)
        self.factory.graph.plot_bbbo(msg)
      elif msg_type == b'S':
        print('System Event: ', msg)
      else:
        print('?: ', msg_type)
      self.factory.broker.return_to_client(data)
    except:
      print('EXCEPTION: message type', data)


# handles all data collection and graphing
class ExchangeGrapher():
  def __init__(self, initial_time):
    self.initial_time = initial_time

    self.buyStartTime = []
    self.buyEndTime = OrderedDict()
    self.buyPriceAxis = []

    self.sellStartTime = []
    self.sellEndTime = OrderedDict()
    self.sellPriceAxis = []

    self.crossTime = []
    self.crossPrice = []

    # data for BBBO [timestamp] = price
    self.bbData = {}
    self.boData = {}
    self.bbData[-1] = -1
    self.boData[-1] = -1

  # creates a horizontal line to represent the order in the book
  def plot_accepted_order(self, msg):
    price = msg['price']/10000
    time_in_force = msg['time_in_force']/10
    timestamp = msg['timestamp']/10000000000
    order_token = msg['order_token']

    if msg['buy_sell_indicator'] == b'B':
      self.buyStartTime.append(timestamp)
      self.buyEndTime[order_token] = timestamp + time_in_force
      self.buyPriceAxis.append(price)

    elif msg['buy_sell_indicator'] == b'S':
      self.sellStartTime.append(timestamp)
      self.sellEndTime[order_token] = timestamp + time_in_force
      self.sellPriceAxis.append(price)

  # cuts the horizontal line short, and puts cross to represent cross in book
  def plot_executed_order(self, msg):
    price = msg['execution_price']/10000
    timestamp = msg['timestamp']/10000000000
    order_token = msg['order_token']

    self.crossPrice.append(price)
    self.crossTime.append(timestamp)
    if order_token in self.buyEndTime:
      self.buyEndTime[order_token] = timestamp
    if order_token in self.sellEndTime:
      self.sellEndTime[order_token] = timestamp

  # cuts the horizontal line short, to represent cancellation
  def plot_cancelled_order(self, msg):
    timestamp = msg['timestamp']/10000000000
    order_token = msg['order_token']

    if order_token in self.buyEndTime:
      self.buyEndTime[order_token] = timestamp
    if order_token in self.sellEndTime:
      self.sellEndTime[order_token] = timestamp


  # datapoints are added twice to make graphing easier
  def plot_bbbo(self, msg):
    timestamp = msg['timestamp']/10000000000
    bid_price = msg['best_bid']/10000
    ask_price = msg['best_ask']/10000

    if (bid_price != 0):
      self.bbData[timestamp] = bid_price
    else:
      self.bbData[timestamp] = np.nan

    if (ask_price < 200000):
      self.boData[timestamp] = ask_price
    else:
      self.boData[timestamp] = np.nan

  def graph_results(self):
    plt.hlines(self.buyPriceAxis, self.buyStartTime, self.buyEndTime.values(), color ="red", linewidth=0.5, label="Bid")
    plt.hlines(self.sellPriceAxis, self.sellStartTime, self.sellEndTime.values(), color ="blue", linewidth=0.5, label="Offer")

    plt.scatter(self.crossTime, self.crossPrice, s=7, linewidth=1, marker = "x", label="Order Execution")
    pickle.dump(self.crossTime, open("crossTime.pickle", "wb"))
    pickle.dump(self.crossPrice, open("crossPrice.pickle", "wb"))


  def graph_results_bbo(self):
    # list manipulation to make the graphical points
    bb = sorted(self.bbData.items())
    bbTime = [key for (key, value) in bb for i in range(2)]
    bbPrice = [value for (key, value) in bb for i in range(2)]

    bo = sorted(self.boData.items())
    boTime = [key for (key, value) in bo for i in range(2)]
    boPrice = [value for (key, value) in bo for i in range(2)]

    plt.plot(bbTime[3:-1], bbPrice[2:-2], linewidth=.7, color="red", label="Best Bid")
    plt.plot(boTime[3:-1], boPrice[2:-2], linewidth=.7, color="blue", label="Best Offer")

  def time(self, time):
    return time - self.initial_time

class ExchangeFactory(ClientFactory):
  protocol = Exchange

  def __init__(self, broker):
    self.broker = broker
    self.graph = ExchangeGrapher(self.broker.initial_time)


  def fit(n):
    return (n - cda_crossTime[0]) * 10

  cda_crossTime = list(map(fit, cda_crossTime))

  def stopFactory(self):
    self.graph.graph_results()
    plt.title("Exchange and Order Executions (FBA)")
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    #plt.show()

    self.graph.graph_results_bbo()
    plt.title("BBBO Activity (CDA)")
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    plt.show()
