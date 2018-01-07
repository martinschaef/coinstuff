import pandas as pd
import pandas_datareader as pdr
import datetime
import matplotlib.pyplot as plt 
import pylab

"""
This one looks like a more reasonable tutorial using Yahoo data and pandas.

"""

# We will look at stock prices over the past year, starting at January 1, 2016
start = datetime.datetime(2017,1,1)
end = datetime.date.today()
 
# Let's get Apple stock data; Apple's ticker symbol is AAPL
# First argument is the series we want, second is the source ("yahoo" for Yahoo! Finance), third is the start date, fourth is the end date
btc = pdr.get_data_yahoo("BTC-USD", start, end)
 
print btc.head()


pylab.rcParams['figure.figsize'] = (15, 9)
btc["Adj Close"].plot(grid = True)

plt.show()