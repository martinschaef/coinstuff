#!/usr/bin/env python
import sys, random
import gdax
import time
from secret_keys import key, b64secret, sbkey, sbsecret, passphrase
import traceback

from collections import deque

from decimal import *
from datetime import datetime, date, timedelta
import dateutil.parser
from operator import itemgetter

products = ['ETH-USD', 'BTC-USD', 'BCH-USD', 'LTC-USD']
auth_client = gdax.AuthenticatedClient(key, b64secret, passphrase)


class TradingBot:
  def __init__(self, auth_client, product, usd_limit=200.0):
    self.granularity_in_seconds = 60
    self.auth_client = auth_client
    self.product = product
    self.usd_limit = usd_limit
    self.history_queue = deque(maxlen=10)
    self.last_price = -1000

    self.read_historic_data()

  def read_historic_data(self):
    public_client = gdax.PublicClient()
    historic_rates = public_client.get_product_historic_rates(self.product, granularity=self.granularity_in_seconds)
    sum_volume = 0.0
    sum_close = 0.0
    sum_high = 0.0
    sum_low = 0.0
    for (timestamp, low, high, open_val, close_val, volume) in reversed(historic_rates):
      sum_volume+=volume
      sum_close+=close_val
      sum_high+=high
      sum_low+=low
      self.history_queue.append(float(close_val))

    avg_low = sum_low/float(len(historic_rates))
    avg_high = sum_high/float(len(historic_rates))

    if len(historic_rates)>0:
      latest_rate=historic_rates[0]
      self.last_price=float(latest_rate[4])
      print (historic_rates[0])
    print ("{} Avg low {}, avg high with avg volume of {}".format(datetime.fromtimestamp(timestamp), avg_low, avg_high, sum_volume/len(historic_rates)))
    pass

  def fetch_data(self):
    public_client = gdax.PublicClient()
    trade = public_client.get_product_ticker(product_id=self.product)
    price = float(trade['price'])
    volume = float(trade['volume'])
    timestamp = trade['time']

    self.history_queue.append(price)

    print("Asking price {} delta {} with volume {}".format(price, price - self.last_price, volume))
    self.last_price = price

    print (self.history_queue)
    time.sleep(self.granularity_in_seconds)

btcbot = TradingBot(auth_client, 'BTC-USD')

while True:
  btcbot.fetch_data()

sys.exit(0)
