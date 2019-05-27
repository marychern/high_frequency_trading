from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import reactor
from OuchServer.ouch_messages import OuchClientMessages
from random import randrange
import time
from message_handler import decodeServerOUCH, decodeClientOUCH
import random
import numpy
import csv
from inventory import Inventory

# -----------------------
# RandomTraderClient class: sends orders to the broker
# -----------------------
class RandomTraderClient(Protocol):

    def __init__(self, inventory):
        self.inventory = inventory
        self.time = []
        self.market_id = []
        self.price = []
        self.time_in_force = []
        self.buy_sell_indicator = []
        self.i = 0
        self.line_count = 0

    def connectionMade(self, latency = 0.3):
        t = 0
        self.readCSVorder()
        for x in range(1,58):
            # if t==0:
            # send order every 4 sec
            reactor.callLater(t+latency, self.sendCSVorder)
            t += 4
            # else:
            #     reactor.callLater(t, self.sendCSVorder)
            #     t += 4

    def readCSVorder(self):
        with open('simulating_arrivals_for_call_on_jan_31_2019.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if len(row) == 0:
                    continue
                # disregard the first line of the csv file
                if self.line_count == 0:
                    self.line_count += 1
                #read in the data
                else:
                    self.time.append(row[0])
                    self.market_id.append(row[1])
                    self.price.append(row[2])
                    self.time_in_force.append(row[3])
                    self.buy_sell_indicator.append(row[4])
                    self.line_count += 1

    def sendCSVorder(self):
        order = OuchClientMessages.EnterOrder(
            order_token='{:014d}'.format(0).encode('ascii'),
            buy_sell_indicator=self.buy_sell_indicator[self.i],
            shares=b'1',
            stock=b'AMAZGOOG',
            price=self.price[self.i],
            time_in_force=self.time_in_force[self.i],
            firm=b'OUCH',
            display=b'N',
            capacity=b'O',
            intermarket_sweep_eligibility=b'N',
            minimum_quantity=1,
            cross_type=b'N',
            customer_type=b' ')
        # increment through the orders
        self.i += 1
        #self.transport.write(bytes(order))
        print("Sent order: ", order)

    # def sendRandomOrder(self):
    #     # TODO: check this matches paper equations?
    #
    #     # range 0.0 to 1.0
    #     randomNum = random.random()
    #
    #     prob_buy = 0.5
    #     buy_sell_indicator = 'S'
    #     if (randomNum < prob_buy):
    #         buy_sell_indicator = 'B'
    #
    #     shares_rate_avg = 150
    #     shares = numpy.random.poisson(shares_rate_avg)
    #
    #     mean_price = 200
    #     sd = 2
    #     price = round(numpy.random.normal(mean_price,sd))
    #
    #     order = OuchClientMessages.EnterOrder(
    #         order_token='{:014d}'.format(0).encode('ascii'),
    #         buy_sell_indicator=buy_sell_indicator.encode(),
    #         shares=shares,
    #         stock=b'AMAZGOOG',
    #         price=price,
    #         time_in_force=randrange(0,99999),
    #         firm=b'OUCH',
    #         display=b'N',
    #         capacity=b'O',
    #         intermarket_sweep_eligibility=b'N',
    #         minimum_quantity=1,
    #         cross_type=b'N',
    #         customer_type=b' ')
    #     self.transport.write(bytes(order))
    #     print("Sent order: ", order)

    def dataReceived(self, data):
        ch = chr(data[0]).encode('ascii')
        if (ch == b'#'):
            print("BB/BO: ", data)
        else:
            msg_type, msg = decodeServerOUCH(data)
            if msg_type == b'A':
                self.inventory.confirmedOrder(
                    msg['order_token'],
                    msg['buy_sell_indicator'],
                    msg['shares'],
                    msg['price']
                )

            elif msg_type == b'E':
                print('executed order')
                self.inventory.executedOrder(
                    msg['order_token'],
                    msg['executed_shares']
                )
            self.inventory.printCurrentPositionDetailed()

# -----------------------
# Main function
# -----------------------
def main():
    inventory = Inventory(100)
    def protocol():
        RTC_instance = RandomTraderClient(inventory)
        # Read in file
        #RTC_instance.readCSVorder()
        # Return RTC instance after reading csv file
        return RTC_instance
    factory = ClientFactory()
    factory.protocol = protocol
    reactor.connectTCP("localhost", 8000, factory)
    reactor.run()

if __name__ == '__main__':
    main()
