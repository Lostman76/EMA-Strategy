import ta.momentum
import ta.trend
import ta.volume
from Keys import api, secret, accountType
from pybit.unified_trading import HTTP
import pandas as pd
import ta 
import time
from Bybit import BybitClient
import numpy as np

session  = BybitClient(api, secret, accountType)

symbols = ["BTCUSDT","ETHUSDT"]

tp = 0.012 # TP = 1.2%
timeframe = 15 # 15 minutes
mode = 1 # 1- isolated, 0-cross
leverage = 10
qty = float(session.get_balance())*0.5
def close_p(symbol, timeframe):
    close_price = session.get_candles(symbol=symbol, timeframe = 15, limit=1000)['Close'].iloc[-2]
    return close_price

def close_c(symbol, timeframe):
    close = session.get_candles(symbol=symbol, timeframe = 15, limit=1000)['Close']
    return close
def get_balance():
    balance = session.get_wallet_balance(accountType = "Contract", coin = "USDT")['result']['list'][0]['coin'][0]['walletBalance']
    balance = float(balance)
    print(f'Balance : {get_balance} USDT')


def Indicator_signal(symbol):
    kl = session.get_candles(symbol, timeframe)
    ema_9 = ta.trend.ema_indicator(session.get_candles(symbol=symbol, timeframe=15, limit=1000)['Close'], window=9)
    ema_15 = ta.trend.ema_indicator(session.get_candles(symbol=symbol, timeframe=15, limit=1000)['Close'], window=15)
    ema_20 = ta.trend.ema_indicator(session.get_candles(symbol=symbol, timeframe=15, limit=1000)['Close'], window= 20)
    ema_200 = ta.trend.ema_indicator(kl.Close, window= 200)
    # dif = abs
    # (abs(float(kl.Close.iloc[-1]) - float(ema_20.iloc[-1])) >= 0.04)
    # print(rsi)
    condition1 = (ema_9.iloc[-2] > ema_15.iloc[-2]) & (ema_15.iloc[-2] > ema_20.iloc[-2])
    condition2 = ((ema_9.iloc[-2] > ema_15.iloc[-2]) & (ema_15.iloc[-2] > session.Last_traded_price(symbol, timeframe=15,limit=1)) & (session.Last_traded_price(symbol, timeframe=15,limit=1) > ema_20.iloc[-2])) | \
                 ((ema_9.iloc[-2] > session.Last_traded_price(symbol, timeframe=15,limit=1)) & (session.Last_traded_price(symbol, timeframe=15,limit=1) > ema_15.iloc[-2]) & (ema_15.iloc[-2] > ema_20.iloc[-2])) | \
                 ((ema_9.iloc[-2] > ema_15.iloc[-2]) & (ema_15.iloc[-2] > ema_20.iloc[-2]) & (ema_20.iloc[-2] > session.Last_traded_price(symbol, timeframe=15,limit=1)))

    if condition1.any() and condition2.any():
        res = 0
        for i in range(1, 10):
            if ((close_c(symbol, timeframe=15).iloc[-i-1] - ema_15.iloc[-i-1]) / ema_15.iloc[-i-1]) > 0.01:
                res += 1
        if res > 0:
            return "up"

    condition3 = (ema_9.iloc[-2] < ema_15.iloc[-2]) & (ema_15.iloc[-2] < ema_20.iloc[-2])
    condition4 = ((ema_9.iloc[-2] < ema_15.iloc[-2]) & (ema_15.iloc[-2] < session.Last_traded_price(symbol, timeframe=15,limit=1)) & (session.Last_traded_price(symbol, timeframe=15,limit=1) < ema_20.iloc[-2])) | \
                 ((ema_9.iloc[-2] < session.Last_traded_price(symbol, timeframe=15,limit=1)) & (session.Last_traded_price(symbol, timeframe=15,limit=1) < ema_15.iloc[-2]) & (ema_15.iloc[-2] < ema_20.iloc[-2])) | \
                 ((ema_9.iloc[-2] < ema_15.iloc[-2]) & (ema_15.iloc[-2] < ema_20.iloc[-2]) & (ema_20.iloc[-2] < session.Last_traded_price(symbol, timeframe=15,limit=1)))

    if condition3.any() and condition4.any():
        res = 0
        for i in range(1, 10):
            if (abs(close_c(symbol, timeframe=15).iloc[-i-1] - ema_15.iloc[-i-1]) / ema_15.iloc[-i-1]) > 0.01:
                res += 1
        if res > 0:
            return "down"

    return "no signal"
    # print(ema_9)
    # print(ema_15)
    # print(ema_20)

        

# Rsi_signal(symbol = "INJUSDT")

def vol_oi_signal(symbol):
    oi = session.Open_interest(symbol)['openInterest']
    oi_numeric = pd.to_numeric(oi, errors='coerce')
    oi_sma = np.mean(oi_numeric[-20:])
    volume = session.get_candles(symbol, timeframe, limit=200)['Volume']
    vol_numeric = pd.to_numeric(volume, errors='coerce')
    vol_sma = np.mean(vol_numeric[-20:])
    
    if (oi_numeric.iloc[-1]>oi_sma) and vol_numeric.iloc[-1] > vol_sma:
        return "up"
    elif (oi_numeric.iloc[-1]<oi_sma) and vol_numeric.iloc[-1] < vol_sma:
        return "down"
    else:
        return "none"
def Funding_rate_signal(symbol):
    Fr= session.get_funding_rates(symbol)['fundingRate']
    Fr_numeric = pd.to_numeric(Fr, errors= 'coerce')
    if Fr_numeric.iloc[-1] >0:
        return "up"
    else:
        return "down"

def williamsR(symbol):
    kl =session.get_candles(symbol, timeframe)
    w = ta.momentum.WilliamsRIndicator(kl.High, kl.low, kl.Close, lbp=24).williams_r()
    ema_w = ta.trend.ema_indicator(w, window = 24)
    if w.iloc[-1]<-99.5:
        return 'up'
    elif w.iloc[-1]>-0.5:
        return 'down'
    elif w.iloc[-1]<-75 and w.iloc[-2]<-75 and w.iloc[-2] < ema_w.iloc[-2] and w.iloc[-1]> ema_w.iloc[-1]:
        return 'up'
    elif w.iloc[-1]>-25 and w.iloc[-2]>-25 and w.iloc[-2] > ema_w.iloc[-2] and w.iloc[-1]< ema_w.iloc[-1]:
        return 'down'
    else:
        return 'none'
    

max_pos = 50 

# symbols = session.get_tickers()


while True:
    balance = session.get_balance()
    if balance ==None:
        print('Cant connect')
    if balance != None:
        balance = float(balance)
        print(f'Balance:{balance} USDT')
        pos = session.get_pos()
        print(f'you have {len(pos)} positoions:{pos}')

        if len(pos)<max_pos:
            for i in symbols:
                pos = session.get_pos()
                if len(pos)>=max_pos:
                    break
                df = session.get_candles(i, timeframe, limit = 1000)
                signal = Indicator_signal(i)


                if signal =='up' :
                    if i not in pos :
                        print(f'Found Buy signal for {i}')
                        # session.set_mode(i)
                        time.sleep(2)
                        session.Place_order_mkt(i, 'buy', mode=0, leverage=10, qty = qty)
                        time.sleep(5)
                            
                    else:
                        print(f"There already exist an long for {i}")
                        print(f"Unrealised PNL: {session.pos_info(symbol=i)}")
                        break
                            # j+=1
                        

                if signal =='down' :
                    if i not in pos: 
                        print(f'Found Sell signal for {i}')
                         # session.set_mode(i)
                        time.sleep(2)
                        session.Place_order_mkt(i, 'sell', mode=0, leverage=10, qty = qty)
                        time.sleep(5)
                            
                    else:
                        print(f"There already exist an Short order for {i}")
                        print(f"Unrealised PNL: {session.pos_info(symbol=i)}")
                        break
                            # j+=1


    print("waiting 2 mins")
    time.sleep(120)
    

