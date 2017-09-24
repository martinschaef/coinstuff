#!/usr/bin/env python
import sys, random
import gdax
import time
from secret_keys import key, b64secret, sbkey, sbsecret, passphrase
import traceback

from decimal import *
from datetime import datetime, date, timedelta
from operator import itemgetter

MIN_USD = 1 # never go below one dollar

SELL_MARKUP = Decimal(1.1)
BUY_MARKUP = Decimal(0.95)

MAX_USD_VOLUMES = {
  "ETH-USD": 300.00,
  "BTC-USD": 300.00,
  "LTC-USD": 300.00
}

MIN_COIN_VOLUMES = {
  "ETH-USD": 0.1,
  "BTC-USD": 0.01,
  "LTC-USD": 0.2
}

open_orders = {
  "ETH-USD": [],
  "BTC-USD": [],
  "LTC-USD": []  
}

TIME_DELTA = timedelta(minutes=1)

total_buy_orders = 0
total_sell_orders = 0

SANDBOX_MODE = False


def setup_client(use_sandbox = False):
  """
    returns pair of auth_client and the list of products
  """
  auth_client = None
  products = ['ETH-USD', 'BTC-USD', 'LTC-USD']
  if use_sandbox==False:
    # Set a default product
    auth_client = gdax.AuthenticatedClient(key, b64secret, passphrase)
  else:
    # Use the sandbox API (requires a different set of API access credentials)
    auth_client = gdax.AuthenticatedClient(sbkey, sbsecret, passphrase, 
                                      api_url="https://api-public.sandbox.gdax.com")
    products = ['BTC-USD']
    #buy a test coin
    response = auth_client.buy(type="market", size="0.011", product_id="BTC-USD")
    print(response)
    # example_response={u'status': u'pending', 
    #                   u'post_only': False, 
    #                   u'product_id': u'BTC-USD', 
    #                   u'fill_fees': u'0.0000000000000000', 
    #                   u'funds': u'896.7581085100000000', 
    #                   u'created_at': u'2017-09-04T21:44:20.538677Z', 
    #                   u'executed_value': u'0.0000000000000000', 
    #                   u'id': u'5538a674-f1d5-4c4d-be97-0e3e943fd3e3', 
    #                   u'stp': u'dc', 
    #                   u'settled': False, 
    #                   u'filled_size': u'0.00000000', 
    #                   u'type': u'market', 
    #                   u'side': u'buy', 
    #                   u'size': u'0.01000000'}
    #response = auth_client.sell(type="market", size="0.011", product_id="BTC-USD")
    print(response)

  return auth_client, products

def parse_market_trend(product, time_limit=timedelta(minutes=60)):
  start_time = datetime.now()-time_limit
  rescent_intervals = auth_client.get_product_historic_rates(product, 
    start=start_time.isoformat(), 
    #end=end_time.isoformat(),
    granularity=int(time_limit.seconds))

  if rescent_intervals == None or len(rescent_intervals)<2:
    print("Not enough historic data")
    return None
  sorted_intervals = sorted(rescent_intervals, key=itemgetter(0))
  first_interval = sorted_intervals[0]
  last_interval = sorted_intervals[len(sorted_intervals)-1]

  rescent_change = (Decimal(last_interval[4])-Decimal(first_interval[3]))/Decimal(first_interval[3]) * Decimal(100.0)
  print ("\t{0}-min Open: {1:.2f}".format(time_limit.seconds, float(first_interval[3]) ))
  print ("\t{0}-min Trend: {1:.2f}".format(time_limit.seconds, float(rescent_change)))
  return rescent_change

def parse_account_data(account_data, print_details=False):
  # {
  #     "id": "71452118-efc7-4cc4-8780-a5e22d4baa53",
  #     "currency": "BTC",
  #     "balance": "0.0000000000000000",
  #     "available": "0.0000000000000000",
  #     "hold": "0.0000000000000000",
  #     "profile_id": "75da88c5-05bf-4f54-bc85-5c775bd68254"
  # },
  summary = dict()
  for account in account_data:    
    summary[account["currency"]] = account["available"]
    if print_details==True:
      print ("{}:\t{}".format(account["currency"], account["available"]))
  return summary

def parse_orders(print_orders=False):
  order_pages = auth_client.get_orders()
  summary = dict()
  for order_page in order_pages:
    for order in order_page:
      if print_orders == True:
        print ("ID {}".format(order["id"]))
        print ("\tType {}".format(order["type"]))
        print ("\tSide {}".format(order["side"]))
        print ("\tStatus {}".format(order["status"]))
        print ("\tProduct {}".format(order["product_id"]))
        print ("\tPrice {}".format(order["price"]))
        print ("\tSize {}".format(order["size"]))
      if order["product_id"] not in summary:
        summary[order["product_id"]] = dict()
        summary[order["product_id"]]["buy"] = Decimal(0.0)
        summary[order["product_id"]]["sell"] = Decimal(0.0)
        summary[order["product_id"]]["orders"] = []

      summary[order["product_id"]][order["side"]] += Decimal(order["size"])
      summary[order["product_id"]]["orders"].append(order)
  return summary

def make_buying_decision(product, currency, daily, available_volume, usd_balance):
  global total_buy_orders, open_orders
  # daily_example = {u'volume': u'378263.60096122', 
  #                 u'last': u'308.99000000', 
  #                 u'volume_30day': u'5162694.21402097', 
  #                 u'high': u'354.00000000', 
  #                 u'low': u'285.00000000', 
  #                 u'open': u'352.76000000'}
  """
  Buy market at current rate -5% if the market is down
  """

  # If the market is going down
  current_value = Decimal(daily["last"])
  limit_value = BUY_MARKUP*current_value
  
  expected_cost = Decimal(MIN_COIN_VOLUMES[product])*current_value

  if expected_cost>=usd_balance:
    print ("\tNot enough money to buy. Have {0:.2f} USD but need {1:.2f} USD to buy {2:.2f} {3}".format(usd_balance, expected_cost, MIN_COIN_VOLUMES[product], currency))
    return False

  print ("** buy {0:.4f} {1} at ${2:.2f}".format(MIN_COIN_VOLUMES[product], currency, limit_value))
  response = auth_client.buy(type="limit", 
                              size=str("{0:.4f}".format(MIN_COIN_VOLUMES[product])), 
                              price=str("{0:.2f}".format(limit_value)), 
                              product_id=product)
  open_orders[product].append(response)
  print ("Placed Order: {}".format(response))
  total_buy_orders+=1

  return True

def make_selling_decision(product, currency, daily, market_change):
  global open_orders
  while True:
    # keep iterating over orders.
    # if a order has been closed, removed it, and issue a new sell order with 10% markup
    closed_order = None
    for open_order in open_orders[product]:
      order_details = auth_client.get_order(open_order["id"])
      if order_details and order_details["status"] == "done" and order_details["done_reason"]=="filled":
        closed_order = open_order
        # Issue a new sell order
        new_price = Decimal(order_details["price"]) * SELL_MARKUP

        print ("** sell {0:.4f} {1} at ${2:.2f}}".format(Decimal(order_details["size"]), currency, new_price))
        response = auth_client.sell(type="limit", 
                                    size="{0:.4f}".format(Decimal(order_details["size"])),
                                    price="{0:.2f}".format(new_price),
                                    product_id=product)        
        print ("Placed Order: {}".format(response))
        total_sell_orders+=1        
        break
    if closed_order == None:
      break
    else:
      open_orders[product].remove(closed_order)
      return True

  return False


def populate_order_book():
  global open_orders
  order_summary = parse_orders()
  account_summary = parse_account_data(auth_client.get_accounts())
  
  total_usd = Decimal(account_summary["USD"])

  for product in products:
    if product in order_summary:
      open_orders[product].extend(order_summary[product]["orders"])
    currency = product[:3]
    # get the total number of coins in the account
    product_volume = Decimal(account_summary[currency])
    # add the coins that are currently committed in orders
    if product in order_summary:
      product_volume += Decimal(order_summary[product]["buy"])
      product_volume += Decimal(order_summary[product]["sell"])
    daily = auth_client.get_product_24hr_stats(product)
    usd_volume = product_volume * Decimal(daily["last"])

    while usd_volume < Decimal(MAX_USD_VOLUMES[product]):
      random_delta = float ( random.randrange(75, 100) ) / 100.0
      print ("Trying to buy at {0:.2f}% of market value".format(random_delta))
      limit_price = Decimal(daily["last"]) * Decimal(random_delta)
      limit_volume = Decimal(MIN_COIN_VOLUMES[product])
      print ("** buy {0:.4f} {1} at ${2:.2f}: cost ${3:.2f}".format(limit_volume, currency, limit_price, limit_price*limit_volume))
      total_usd -= limit_price*limit_volume
      if total_usd < Decimal(MIN_USD):
        print ("Running out of money: ${0:.2f}!".format(total_usd))
        break
      usd_volume+=limit_price*limit_volume
      response = auth_client.buy(type="limit", 
                                  size=str("{0:.4f}".format(limit_volume)), 
                                  price=str("{0:.2f}".format(limit_price)), 
                                  product_id=product)
      open_orders[product].append(response)
      print ("Placed Order: {}".format(response))

      pass


########## Main Loop ###############

while True:
  try:
    auth_client, products = setup_client(SANDBOX_MODE)

    if len(open_orders["BTC-USD"])==0 and len(open_orders["LTC-USD"])==0 and len(open_orders["ETH-USD"])==0:
      print("Populating order book.")
      populate_order_book()

    print ("Open BTC orders: {}".format(len(open_orders["BTC-USD"])))
    print ("Open LTC orders: {}".format(len(open_orders["LTC-USD"])))
    print ("Open ETH orders: {}".format(len(open_orders["ETH-USD"])))
    break

    while True:    
      account_data = auth_client.get_accounts()

      order_summary = parse_orders()
      account_summary = parse_account_data(account_data)
      
      total_usd = Decimal(account_summary["USD"])

      total_coin_usd = Decimal(0.0)

      for product in products:
        currency = product[:3]
        print ("=============== {} ================".format(currency))

        # get the total number of coins in the account
        available_volume = Decimal(account_summary[currency])
        volume = available_volume
        # add the coins that are currently committed in orders
        if product in order_summary:
          volume += Decimal(order_summary[product]["buy"])
          volume += Decimal(order_summary[product]["sell"])

        daily = auth_client.get_product_24hr_stats(product)
        #one_hour_trend = parse_market_trend(product, time_limit=timedelta(minutes=60))

        usd_volume = volume * Decimal(daily["last"])

        total_coin_usd += usd_volume
        print("Volume of {}:\t{} {} \t ${}".format(currency, volume, currency, usd_volume))
        print ("\tTotal open order for {}: {}".format(product, len(open_orders[product])))
        daily_change = (Decimal(daily["last"])-Decimal(daily["open"]))/Decimal(daily["open"]) * Decimal(100.0)
        print ("\t24h Open: {0:.2f}".format(float(daily["open"])))
        print ("\t24h Trend: {0:.2f}".format(float(daily_change)))

        if usd_volume < Decimal(MAX_USD_VOLUMES[product]):
          successful = make_buying_decision(product, currency, daily, available_volume, total_usd)          
          if successful == True:
            # print ("Only trade one coin per round. Otherwise we'd have to update the usd balance")
            break
        else:
          print ("\tNot buying because already have {0:.2f} usd of {1}".format(usd_volume, currency))

        if available_volume-Decimal(MIN_USD) > Decimal(MIN_COIN_VOLUMES[product]):
          successful = make_selling_decision(product, currency, daily, available_volume)
          if successful == True:
            break
        else:
          print ("\tNot selling because only have {0:0.2f} {1} but need at least {2}".format(available_volume, currency, MIN_COIN_VOLUMES[product]))



      print ("Total USD balance: {}".format(total_usd))
      print ("Total Coin balance: {}".format(total_coin_usd))
      print (".... sleeping for {}sec ...".format(TIME_DELTA.seconds))
      time.sleep(float(TIME_DELTA.seconds))

      #break
  except KeyboardInterrupt:  
    break
  except:
    e = sys.exc_info()[0]
    print (e) 
    traceback.print_exc()

print("Bye bye")
