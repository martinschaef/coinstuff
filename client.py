#!/usr/bin/env python
import sys
import gdax
import time
from secret_keys import key, b64secret, sbkey, sbsecret, passphrase

from decimal import *

auth_client = None
products = ['ETH-USD', 'BTC-USD', 'LTC-USD']
if True:
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
  example_response={u'status': u'pending', 
                    u'post_only': False, 
                    u'product_id': u'BTC-USD', 
                    u'fill_fees': u'0.0000000000000000', 
                    u'funds': u'896.7581085100000000', 
                    u'created_at': u'2017-09-04T21:44:20.538677Z', 
                    u'executed_value': u'0.0000000000000000', 
                    u'id': u'5538a674-f1d5-4c4d-be97-0e3e943fd3e3', 
                    u'stp': u'dc', 
                    u'settled': False, 
                    u'filled_size': u'0.00000000', 
                    u'type': u'market', 
                    u'side': u'buy', 
                    u'size': u'0.01000000'}
  #response = auth_client.sell(type="market", size="0.011", product_id="BTC-USD")
  print(response)

account_data = auth_client.get_accounts()


def get_account_details(account_data):
  account_map = dict()
  #we count the number of accounts where we sold last.
  total_sell_accounts = 0

  for account in account_data:    
    account_map[account["currency"]] = dict()
    account_map[account["currency"]]["balance"]=account["available"]
    account_history = auth_client.get_account_history(account["id"])

    last_order = None  
    if account_history[0]:
      for history_order in account_history[0]:
        if history_order and history_order["type"]=="match":
          last_order = history_order
          break
        elif history_order and history_order["type"]=="fee":
          # ignore fees
          pass
        elif history_order and history_order["type"]=="transfer":
          # ignore fees
          pass          
        else:
          print("Unknown order type {}".format(history_order))
      if last_order==None:
        continue

      last_order_example = {u'created_at': u'2017-09-04T19:45:00.455528Z', 
                    u'amount': u'-0.0300000000000000', 
                    u'details': {u'order_id': 
                              u'841c5b42-a288-4e54-9887-1ea1619a3693', 
                              u'trade_id': u'5449734', 
                              u'product_id': u'LTC-USD'}, 
                    u'balance': u'0.1081976500000000', 
                    u'type': u'match', 
                    u'id': 268294024}, 

      order_details = auth_client.get_order("{}".format(last_order["details"]["order_id"]))
      order_details_example = {u'done_reason': u'filled', 
                          u'status': u'done', 
                          u'post_only': False, 
                          u'specified_funds': u'10.0000000000000000', 
                          u'product_id': u'ETH-USD', 
                          u'fill_fees': u'0.0299102688000000', 
                          u'funds': u'9.9700897300000000', 
                          u'created_at': u'2017-09-04T19:23:30.976001Z', 
                          u'id': u'ba8501df-baae-4511-9c27-2b8e9fea37ed', 
                          u'stp': u'dc', 
                          u'settled': True, 
                          u'done_at': u'2017-09-04T19:23:30.992Z', 
                          u'executed_value': u'9.9700896000000000', 
                          u'type': u'market', 
                          u'side': u'buy', 
                          u'filled_size': u'0.03126400'}

      if order_details and order_details["status"]=="done" and order_details["done_reason"]=="filled":
        exchange_rate = Decimal(order_details["executed_value"])/Decimal(order_details["filled_size"])
        #print ("Executed {} at {}".format(order_details["side"], exchange_rate))

        account_map[account["currency"]]["side"] = order_details["side"]
        account_map[account["currency"]]["rate"] = exchange_rate
        if account["currency"]!="USD" and order_details["side"]=="sell":
          total_sell_accounts += 1
        pass
  account_map["total_sell_accounts"] = total_sell_accounts
  return account_map


try:
  while True:    
    account_data = auth_client.get_accounts()

    account_details = get_account_details(account_data)

    if account_details == None:
      print("Failed to fetch account info. Sleeping for 10 seconds before retry.")
      sys.sleep(10)
      continue

    total_sell = account_details["total_sell_accounts"]
    total_usd = Decimal(account_details["USD"]["balance"])
    
    next_buy_amount = 0
    if total_sell>0:
      next_buy_amount = total_usd / Decimal(total_sell)

    MAX_BUY_ORDER = 10
    if next_buy_amount>Decimal(MAX_BUY_ORDER):      #!!!!!!!!!!!!!!!!
      next_buy_amount = Decimal(MAX_BUY_ORDER)
      print ("... maxing order at {}".format(next_buy_amount)) 
    print("USD {} available. Max {} orders at {}".format(total_usd, total_sell, next_buy_amount))



    for product in products:      
      ticker = auth_client.get_product_ticker(product_id=product)
      ticker_example = {u'bid': u'308.98', 
                        u'volume': u'378263.60096122', 
                        u'trade_id': 10277778, 
                        u'time': u'2017-09-04T19:00:20.303000Z', 
                        u'ask': u'308.99', 
                        u'price': u'308.99000000', 
                        u'size': u'0.39080539'}

      daily = auth_client.get_product_24hr_stats(product)
      daily_example = {u'volume': u'378263.60096122', 
                      u'last': u'308.99000000', 
                      u'volume_30day': u'5162694.21402097', 
                      u'high': u'354.00000000', 
                      u'low': u'285.00000000', 
                      u'open': u'352.76000000'}

      currency = product[:3]

      current_rate = Decimal(ticker["price"])
      # check if we have a completed order in the history
      if account_details[currency] and "side" in account_details[currency]:
        bought_rate = Decimal(account_details[currency]["rate"])          
        balance = Decimal(account_details[currency]["balance"]) * Decimal(0.95)
        print(">>{} {}\t bought at {}\t. currenlty at: {}".format(currency, balance, bought_rate, current_rate))

        if account_details[currency]["side"]=="buy":
          change = (current_rate / bought_rate * Decimal(100)) - Decimal(100)
          SELL_AT_PERCENT=Decimal(2.0) #!!!!!!!!!!!!!!!!

          print ("\tNext order is sell. Value change: {0:.2f} selling at {1:.2f}".format(change,SELL_AT_PERCENT))

          if change>SELL_AT_PERCENT:
            #print("Balance {}",format(balance))
            #sys.exit(0)
            response = auth_client.sell(type="market", size="{0:.4f}".format(balance), product_id=product)
            print ("Sell sell sell: {}".format(response))

        elif account_details[currency]["side"]=="sell":          
          low = Decimal(daily["low"])
          high = Decimal(daily["high"])
          middle = low + (high-low)*Decimal(0.75)
          print("\tNext order is buy. Buying below {}".format(middle))
          if current_rate<middle:
            buy_amount = Decimal(next_buy_amount)/Decimal(current_rate)*Decimal(0.9)
            response = auth_client.buy(type="market", size=str("{0:.4f}".format(buy_amount)), product_id=product)
            print("Buy buy buy {}".format(response))

        else:
          pass
    time.sleep(10)
    #break
except KeyboardInterrupt:  
  pass

print("Bye bye")