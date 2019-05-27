#from multiprocessing import Process
import multiprocessing as mp
from run_exchange_server import main as l
from broker import main as m
from external_clients import main as n
import configargparse


if __name__ == '__main__':
	mp.set_start_method('spawn')
	a = mp.Process(target=m)
	a.start()

	b = mp.Process(target=n)
	b.start()
