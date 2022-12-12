import robin_stocks.robinhood as robin
import pyotp
import sys
from datetime import datetime
import time
from urllib import request, parse


# log into robinhood
lines = open('../cred.text').read().splitlines()
KEY = lines[0]
EMAIL = lines[1]
PASSWD = lines[2]
CODE = lines[3]
PUSH_KEY = lines[4]
totp = pyotp.TOTP(KEY).now()
login = robin.login(EMAIL, PASSWD, mfa_code=CODE)
now = datetime.now()

# decorator function


def clean_decor(func):
    def inner1():
        print('')
        func()
        print('')
        print('*************************')
        print('')
    return inner1


def clean_decor2(func):
    def decor(crypto, sell_amount, limit_price):
        def inner1(*args, **kwargs):
            print('')
            func(crypto, sell_amount, limit_price, *args, **kwargs)
            print('')
            print('*************************')
            print('')
        return inner1
    return decor

# Function to get the current price of a cryptocurrency


def QUOTE(crypto):
    ct = robin.get_crypto_quote(crypto)
    now = datetime.now()
    current_datetime = now.strftime('%I:%M:%S:%p')
    print(crypto.upper() + ": $" +
          str(ct['bid_price'] + ' | TIME: ' + current_datetime))
    return ct['bid_price']

# Function to sell a specified amount of a cryptocurrency at a given limit price


def SELL(crypto, amount, limit_price):
    r = robin.order_sell_crypto_limit(crypto, amount, limit_price)
    print(f'Selling {amount} of {crypto.upper()} at: ${limit_price}')

# Function to buy a specified amount of a cryptocurrency at a given limit price


def BUY(crypto, amount, limit_price):
    r = robin.order_buy_crypto_limit(crypto, amount, limit_price)
    print(r)
    print(f'Buying {amount} of {crypto.upper()} at: ${limit_price}')


crypto = sys.argv[1:][0].upper()

# Set the amount of crypto to trade
amount = 0
sell_amount = 100


# Set the minimum profit threshold for selling
min_profit_threshold = 0.012

# Initialize the last purchase price
last_purchase_price = 0.096696

# Set the negative profit threshold
neg_profit_threshold = float(last_purchase_price) - \
    (last_purchase_price * min_profit_threshold)

# Set the positive profit threshold
pos_profit_threshold = float(last_purchase_price) + \
    float(last_purchase_price) * min_profit_threshold

# push notifications
sale_push = parse.urlencode(
    {'text': f'DOGE (+)margin of: ${pos_profit_threshold} hit!'}).encode()
buy_push = parse.urlencode(
    {'text': f'DOGE (-)margin of: ${neg_profit_threshold} hit!'}).encode()
sal_req = request.Request(
    f'https://api.chanify.net/v1/sender/{PUSH_KEY}', data=sale_push)
buy_req = request.Request(
    f'https://api.chanify.net/v1/sender/{PUSH_KEY}', data=buy_push)

# Print target margins and current holdings


def buy_status():
    print(f'BUY TARGET: ${neg_profit_threshold}')
    print(f'SELL TARGET: ${pos_profit_threshold}')
    print(f'BUY: {amount}  SELL: {sell_amount}')


# Assign decorators to functions
buy_status = clean_decor(buy_status)
BUY = clean_decor2(BUY)
SELL = clean_decor2(SELL)


while True:
    # Get the current price of the crypto
    current_price = float(QUOTE(crypto))
# If the current price is lower than the last purchase price, buy the crypto
    if current_price < neg_profit_threshold and amount != 0:
        limit_price = round(current_price, 2)
        BUY(crypto, amount, limit_price)
        last_purchase_price = current_price
        amount = 0
        sell_amount = 100
        request.urlopen(buy_req)
# If the current price is higher than the last purchase price plus the minimum profit threshold, sell the crypto
    elif current_price > pos_profit_threshold and sell_amount != 0:
        limit_price = round(current_price, 2)
        SELL(crypto, sell_amount, limit_price)
        last_purchase_price = current_price
        sell_amount = 0
        amount = 100
        request.urlopen(sale_req)
# If the current price is less than or equal to the last purchase price, print target buy price
    elif current_price <= float(last_purchase_price):
        buy_status()
# If the current price is greater than or equal to the last purchase price, print target sell price
    elif current_price >= float(last_purchase_price):
        buy_status()
    time.sleep(10)
