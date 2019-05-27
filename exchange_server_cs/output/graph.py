import matplotlib.pyplot as plt
import pickle


cda_valueAxis = pickle.load(open("cda_valueAxis.pickle", "rb"))
cda_timeAxis = pickle.load(open("cda_timeAxis.pickle", "rb"))

plt.hlines(cda_valueAxis[1:-1], cda_timeAxis[1:-2], cda_timeAxis[2:], linewidth=.7, label="Fundamental Value")
plt.vlines(cda_timeAxis[2:-1], cda_valueAxis[1:], cda_valueAxis[2:], linewidth=.7)


cda_crossPrice = pickle.load(open("cda_crossPrice.pickle", "rb"))
cda_crossTime = pickle.load(open("cda_crossTime.pickle", "rb"))

def fit(n):
	return (n-cda_crossTime[0])*10

cda_crossTime = list(map(fit, cda_crossTime))

plt.hlines(cda_crossPrice[:-2], cda_crossTime[:-2], cda_crossTime[1:], linewidth=.7, color="orange", label="CDA")
plt.vlines(cda_crossTime[1:-1], cda_crossPrice, cda_crossPrice[1:], linewidth=.7, color="orange")


fba_crossPrice = pickle.load(open("fba_crossPrice.pickle", "rb"))
fba_crossTime = pickle.load(open("fba_crossTime.pickle", "rb"))

def fit(n):
	return (n-fba_crossTime[0])*10

fba_crossTime = list(map(fit, fba_crossTime))

plt.hlines(fba_crossPrice[:-1], fba_crossTime[:-1], fba_crossTime[1:], linewidth=.7, color="red", label="FBA")
plt.vlines(fba_crossTime[1:-1], fba_crossPrice, fba_crossPrice[1:], linewidth=.7, color="red")

plt.title("Price Volatility (CDA vs FBA)")
plt.ylabel("Price")
plt.xlabel("Time")
plt.legend()
plt.show()