#!/usr/bin/env python
import sys, random
import gdax
import time
from secret_keys import key, b64secret, sbkey, sbsecret, passphrase
import traceback

from datetime import date
import matplotlib.pyplot as plt
import numpy as np

products = ['ETH-USD', 'BTC-USD', 'LTC-USD']

public_client = gdax.PublicClient()

def get_rates(product):
  # https://docs.gdax.com/#get-historic-rates
  # must be in {60, 300, 900, 3600, 21600, 86400}
  # Returns tuples of:
  # * time bucket start time
  # * low lowest price during the bucket interval
  # * high highest price during the bucket interval
  # * open opening price (first trade) in the bucket interval
  # * close closing price (last trade) in the bucket interval
  # * volume volume of trading activity during the bucket interval
  historic_rates = public_client.get_product_historic_rates(product, granularity=3600)
  prices_list = list()
  date_list = list()
  point_list = list()

  for entry in historic_rates:
    time, low, high, open_val, close_val, volume = entry
    entry_date = date.fromtimestamp(time)  
    avg_price = low + (high-low)/2.0
    print("{}:\t{}".format(time, avg_price))
    prices_list.append(avg_price)
    date_list.append(time)
    point_list.append([entry_date, avg_price])

  curve_points = np.array(prices_list)
  return date_list, prices_list

plt.figure(1) 
date_list, prices_list = get_rates('ETH-USD')
plt.subplot(311) 
plt.plot(date_list, prices_list, "g")
plt.ylabel('ETH')

plt.subplot(312) 
date_list, prices_list = get_rates('BTC-USD')
plt.plot(date_list, prices_list, "r")
plt.ylabel('BTC')

plt.subplot(313) 
date_list, prices_list = get_rates('LTC-USD')
plt.plot(date_list, prices_list, "b")
plt.ylabel('LTC')
plt.show()