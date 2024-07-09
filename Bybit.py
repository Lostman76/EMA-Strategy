from pybit.unified_trading import HTTP
import pandas as pd 
import ta
import time
import requests
import pprint
import numpy as np
import ta.momentum
import ta.trend
import ta.volume

class BybitClient:

    def __init__(self, api, secret, accounttype):
        self.api= api
        self.secret = secret
        self.accountType = accounttype
        self.session = HTTP(api_key = self.api, api_secret = self.secret, testnet = False)

    def get_balance(self):
        balance = self.session.get_wallet_balance(accountType = self.accountType, coin = "USDT")['result']['list'][0]['coin'][0]['walletBalance']
        # DF = pd.DataFrame(balance['result']['list'])
        balance = round(float(balance),3)
        # print(DF)
        return balance
        
    def get_pos(self):
        positions = self.session.get_positions(category = 'linear', settleCoin = 'USDT', recv_window = 40000)['result']['list']
        pos=[]
        for i in positions:
            pos.append(i['symbol'])
        return pos
    
    def get_pnl(self, limit = 100):
        pnl = self.session.get_closed_pnl(category = 'linear', limit = limit, recv_window = 40000)['result']['list']
        pndl = 0
        for i in pnl:
            pndl +=float(i['closedPnl'])
            return round(pndl, 4)
        
    def get_unr_pnl(self):
        unrl_pnl = self.session.get_positions(category = 'linear', settleCoin = 'USDT', recv_window = 10000)['result']['list']
        unr_pl = 0
        for i in unrl_pnl:
            unr_pl +=float(i['unrealisedPnl'])
        return round(unr_pl, 2)
    
    def get_tickers(self):
        tick = self.session.get_tickers(category = 'linear', recv_window = 20000)['result']['list']
        symbols = []
        for i in tick:
            # if 'USDT' in i['symbol'] and not 'USDC' in i['symbol']:
            symbols.append(i['symbol'])  
        return symbols 
    
    def get_candles(self, symbol, timeframe, limit = 1000):
        candles = self.session.get_kline(category = 'linear', symbol = symbol, interval = timeframe, limit = limit, recv_window = 7000)['result']['list']
        df =pd.DataFrame(candles)
        df.columns = ['Time', 'Open', 'High', "low", 'Close', 'Volume', 'Turnover']
        df = df.set_index('Time')
        df = df.astype(float)
        df=df[::-1]
        return df
    
    def Open_interest(self, symbol):
        oi = self.session.get_open_interest(category = "linear", symbol = symbol, intervalTime = "15min", limit = 200)['result']['list']
        df = pd.DataFrame(oi)
        df=df[::-1]
        return df
    
    def get_funding_rates(self, symbol):
        Fr = self.session.get_funding_rate_history(category = "linear", symbol = symbol)['result']['list']
        df = pd.DataFrame(Fr)
        df = df[::-1]
        return df
    
    def Last_traded_price(self, symbol, timeframe, limit = 1):
        Cp = self.session.get_mark_price_kline(category = "linear", symbol = symbol, interval = timeframe, limit =1, recv_window = 7000)['result']['list'][0][4]
        ltp = float(Cp)
        return ltp
            
        
    
    
    def get_instruments_precision(self, symbol):
        info = self.session.get_instruments_info(category = 'linear', symbol = symbol, recv_window = 10000)['result']['list'][0]
        price = info['priceFilter']['tickSize']
        if '.' in price:
            price = len(price.split('.')[1])
        else:
            price = 0
        
        qty = info['lotSizeFilter']['qtyStep']
        if '.' in qty:
            qty = len(qty.split('.')[1])
        else:
            qty = 0

        return price, qty
        # pprint.pprint(info)

    def get_max_lev(self, symbol):
        lev = self.session.get_instruments_info(category = 'linear', symbol = symbol, recv_window = 10000)['result']['list']['leverageFilter']['maxLeverage']
        return float(lev)
    
    # def set_mode(self, symbol, mode = 1, leverage = 10):
    #     mod = self.session.switch_margin_mode(category = 'linear', symbol = symbol, tradeMode = str(mode), buyLeverage = str(leverage), 
    #     sellLeverage = str(leverage), recv_window = 10000)

    #     if mod['retMsg'] == "OK":
    #         if mode ==1:
    #             print(f'[{symbol}] Changed margin mode to Isolated')
    #         if mode ==0:
    #             print(f'[{symbol}] Changed margin mode to Cross')

    # def set_lev(self, symbol, leverage = 10):
    #     lvg = self.session.set_leverage(category = 'linear', symbol = symbol,
    #                                     buyLeverage = str(leverage), sellLeverage = str(leverage), recv_window = 10000)  
    #     if lvg['retMsg'] =="OK":
    #         print(f'[{symbol}] changed leverage to {leverage}')

    # kl = BybitClient.get_candles(symbol="BTCUSDT", timeframe=15, limit=1000)
    
    def ema(self, symbol, timeframe):      
        return ta.trend.ema_indicator(self.get_candles(symbol=symbol, timeframe=15, limit=1000)['Close'], window=20)
    sl = 0.005
    def pos_info(self,symbol):
        Pi = self.session.get_positions(category = "linear", symbol= symbol)["result"]["list"][1]['unrealisedPnl']
        return Pi


    def Place_order_mkt(self, symbol, side, mode, leverage, qty, tp = 0.012, sl = sl):
        # self.set_mode(symbol, mode, leverage)
        mode = 0
        time.sleep(0.5)

        # self.set_lev(symbol, leverage)
        leverage = 10
        time.sleep(1)

        price_precision = self.get_instruments_precision(symbol)[0]
        qty_precision = self.get_instruments_precision(symbol)[1]

        mark_price = self.session.get_tickers(category = "linear", symbol = symbol, recv_window = 10000)['result']['list'][0]['markPrice']
        mark_price = float(mark_price)
        kl = self.get_candles(symbol=symbol, timeframe=15)
        ema_20 = ta.trend.ema_indicator(kl.Close, window= 20)

        print(f'Placing {side} order for {symbol}, Mark Price : {mark_price}')
        order_qty = round(qty/mark_price, qty_precision)
        time.sleep(2)


        if side =="buy":
            tp_price = round(mark_price + mark_price*tp, price_precision)
            sl_price = round(self.ema(symbol, timeframe=15).iloc[-1] - (self.ema(symbol, timeframe=15).iloc[-1])*sl, price_precision)

            ord = self.session.place_order(category = 'linear', symbol = symbol, side = 'Buy', orderType = "Market", positionIdx=1,
                                           qty = order_qty, takeProfit = tp_price, stopLoss = sl_price, 
                                           tpTriggerBy = 'Market', slTriggerBy = 'Market', recv_window =10000)
            
            print(ord['retMsg'])


        if side =="sell":
            tp_price = round(mark_price - mark_price*tp, price_precision)
            sl_price = round(self.ema(symbol, timeframe=15).iloc[-1] + (self.ema(symbol, timeframe=15).iloc[-1])*sl, price_precision)

            ord = self.session.place_order(category = 'linear', symbol = symbol, side = 'Sell', orderType = "Market", positionIdx = 2,
                                           qty = order_qty, takeProfit = tp_price, stopLoss = sl_price, 
                                           tpTriggerBy = 'Market', slTriggerBy = 'Market', recv_window =10000)
            
            print(ord['retMsg'])

    def place_order_limit(self, symbol, side, mode, leverage, qty, tp = 0.012, sl = 0.005):
        # self.set_mode(symbol, mode, leverage)
        mode = 0
        time.sleep(0.5)
        # self.set_lev(symbol, leverage)
        leverage = 10
        time.sleep(1)

        price_precision = self.get_instruments_precision(symbol)[0]
        qty_precision = self.get_instruments_precision(symbol)[1]

        limit_price = self.session.get_tickers(category = "linear", symbol = symbol, recv_window = 10000)['result']['list'][0]['lastPrice']
        limit_price = float(limit_price)

        print(f'Placing {side} order for {symbol}, Limit Price : {limit_price}')
        order_qty = round(qty/limit_price, qty_precision)
        time.sleep(2)


        if side =="buy":
            tp_price = round(limit_price+limit_price*tp, price_precision)
            sl_price = round(limit_price - limit_price*sl, price_precision)

            ord = self.session.place_order(category = 'linear', symbol = symbol, side = 'Buy', orderType = "Limit", 
                                           qty = order_qty, takeProfit = tp_price, stopLoss = sl_price, 
                                           tpTriggerBy = 'LastPrice', slTriggerBy = 'LastPrice', recv_window =10000)
            
            print(ord['retMsg'])


        if side =="sell":
            tp_price = round(limit_price - limit_price*tp, price_precision)
            sl_price = round(limit_price + limit_price*sl, price_precision)

            ord = self.session.place_order(category = 'linear', symbol = symbol, side = 'Sell', orderType = "Market", 
                                           qty = order_qty, takeProfit = tp_price, stopLoss = sl_price, 
                                           tpTriggerBy = 'LastPrice', slTriggerBy = 'LastPrice', recv_window =10000)
            
            print(ord['retMsg'])

    


        
