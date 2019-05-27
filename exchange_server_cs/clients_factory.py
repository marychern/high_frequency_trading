from twisted.internet.protocol import Protocol, ServerFactory
from message_handler import decodeClientOUCH
import matplotlib.pyplot as plt
import csv

class Client(Protocol):
    # if a connection is made, add self to the broker
    def connectionMade(self):
        self.factory.broker.clients.append(self)

    # if data received, plot it and then send to exchange
    # get_order_token, logs this order to this client
    def dataReceived(self, data):
        msg_type, msg = decodeClientOUCH(data)
        if msg_type == b'O':
            self.factory.graph.plot_enter_order(msg)

            client_id = self.factory.broker.clients.index(self)
            order_token = self.factory.broker.assign_order_token(client_id)
            msg['order_token'] = order_token
            self.factory.broker.exchange.transport.write(bytes(msg))

# handles all data collection and graphing
class ClientsGrapher():
    def __init__(self, time):
        self.time = time

        self.buyStartTime = []
        self.buyEndTime = []
        self.buyPriceAxis = []

        self.sellStartTime = []
        self.sellEndTime = []
        self.sellPriceAxis = []
        self.count = 0

    def plot_enter_order(self, msg):
        price = msg['price']
        time_in_force = msg['time_in_force']
        if msg['buy_sell_indicator'] == b'B':
            self.buyStartTime.append(self.time())
            self.buyEndTime.append(self.time() + time_in_force)
            self.buyPriceAxis.append(price/10000)

        elif msg['buy_sell_indicator'] == b'S':
            self.sellStartTime.append(self.time())
            self.sellEndTime.append(self.time() + time_in_force)
            self.sellPriceAxis.append(price/10000)

    def graph_results(self):
        plt.hlines(self.buyPriceAxis, self.buyStartTime, self.buyEndTime, color ="red", linewidth=0.5, label="Bid")
        plt.hlines(self.sellPriceAxis, self.sellStartTime, self.sellEndTime, color ="blue", linewidth=0.5, label="Offer")

        # dump to csv file
        with open('data_points.csv', mode='w') as data_file:
            data_writer = csv.writer(data_file, delimiter='\n', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            data_writer.writerow(["ORDERS FOR BUYERS"])
            data_writer.writerow(self.buyPriceAxis)
            data_writer.writerow(["ORDERS FOR SELLERS"])
            data_writer.writerow(self.sellPriceAxis)
        data_file.close()
        

# persistent factory to handle all client connections
class ClientsFactory(ServerFactory):
    protocol = Client

    def __init__(self, broker):
        self.broker = broker
        self.graph = ClientsGrapher(self.broker.time)

    def stopFactory(self):
        # graph the results
        self.broker.end_time = self.broker.time()
        self.graph.graph_results()
        self.broker.underlyingValueFeed.graph_results(self.broker.end_time)
        plt.title("Traders and Fundamental Value")
        plt.xlabel('Time')
        plt.ylabel('Price')
        plt.legend()
        #plt.show()
