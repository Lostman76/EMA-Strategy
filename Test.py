from Keys import accountType, secret, api
import time
import ta
from threading import Thread
from Bybit import BybitClient

session  = BybitClient(api, secret, accountType)
timeframe = 15
tp = 0.015
max_positions =100
symbol = "BTCUSDT"

df = session.pos_info(symbol=symbol)
print(df)

