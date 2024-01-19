# Algo Trading with Himmat
    # Strategy  - EMA Crossover 
    # Entry     - EMA Crossover Above (Call), EMA Crossover Below (Put)
    # Exit      - Opp. Side EMA Crossover

import datetime as dt
import pandas as pd
import time
from configparser import ConfigParser
from kiteconnect import KiteConnect

# read config.ini
config = ConfigParser()
config.read('config.ini')
# Zerodha_APP details section
api_key         = config.get('Zerodha_APP', 'api_Key')
api_secret      = config.get('Zerodha_APP', 'api_secret')
kite            = KiteConnect(api_key=api_key)
print(kite.login_url()) # Open the Url in browser and copy request token 
# https://kite.zerodha.com/connect/login?api_key=*********&v=3
request_token   = "erKTxgzTAUWlonoEUA1uuuE10f7gFGji"

data            = kite.generate_session(request_token, api_secret=api_secret)
access_token    = data["access_token"]
kite.set_access_token(access_token)

# initialize variables
is_long_trade       = False
is_short_trade      = False
ema_short_period    = 13
ema_long_period     = 34
option_symbol       = 'BANKNIFTY24117'
trade_quantity      = 15

def placeOrder(symbol,BorS):
	orderId = kite.place_order(
            variety='regular',
            exchange='NFO',
            tradingsymbol=symbol,
            transaction_type=BorS,
            quantity=trade_quantity,
            product='NRML',
            order_type='MARKET',
            validity='DAY'
        )
	print('Order Placed :: '+str(symbol)+' Transaction :: '+str(BorS)+' Id :: '+str(orderId))
	return orderId

def run(data):
    global is_long_trade, is_short_trade
    
    df                  = pd.DataFrame(data)
    df['ema_short']     = df['close'].ewm(span=ema_short_period, adjust=False).mean()
    df['ema_long']      = df['close'].ewm(span=ema_long_period, adjust=False).mean()

    print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
          " Candle -2 :: 13 EMA : "+str(df['ema_short'].iloc[-2])+" 34 EMA : "+str(df['ema_long'].iloc[-2]))
    print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
          " Candle -1 :: 13 EMA : "+str(df['ema_short'].iloc[-1])+" 34 EMA : "+str(df['ema_long'].iloc[-1]))

    # Check for EMA crossover above for Call Buy
    if df['ema_short'].iloc[-2] < df['ema_long'].iloc[-2] and df['ema_short'].iloc[-1] > df['ema_long'].iloc[-1]:
        # EMA crossover to the upside
        print('Exit put position if open')
        if is_short_trade:
            print('EMA Crossover Above! Closing Put Position')
            orderId         = placeOrder(put_symbol, 'SELL')     
            is_short_trade  = False

        if not is_long_trade:
            print("Call Buy Entry : ")
            round_to_strike     = int(round(float(df['close'].iloc[-1]), -2)) # round closed price to nearest strike price
            call_symbol         = str(option_symbol)+str(round_to_strike)+'CE'
            orderId             = placeOrder(call_symbol, 'BUY')
            is_long_trade       = True

    # Check for EMA crossover below for Put Buy
    elif df['ema_short'].iloc[-2] > df['ema_long'].iloc[-2] and df['ema_short'].iloc[-1] < df['ema_long'].iloc[-1]:
        # EMA crossover to the downside
        print('Exit call position if open')
        if is_long_trade:
            print('EMA Crossover Below! Closing Call Position')
            orderId         = placeOrder(call_symbol, 'SELL')     
            is_long_trade   = False

        if not is_short_trade:
            print("Put Buy Entry : ")
            round_to_strike = int(round(float(df['close'].iloc[-1]), -2)) # round closed price to nearest strike price
            put_symbol      = str(option_symbol)+str(round_to_strike)+'PE'
            orderId         = placeOrder(put_symbol, 'BUY')
            is_short_trade  = True

# Get Bank Nifty Instrument Token to Fetch Historical Data
banknifty_symbol    = 'NSE:NIFTY BANK'
instruments         = kite.instruments('NSE')
instrumentsDf       = pd.DataFrame(instruments)
indicesDf           = instrumentsDf[instrumentsDf['segment'] == 'INDICES']
bankNiftyDf         = indicesDf[indicesDf['name'] == 'NIFTY BANK']
BNInstrumentToken   = bankNiftyDf['instrument_token'].iloc[0]

while True:
    to_date         = dt.datetime.now().date()
    from_date       = to_date - dt.timedelta(days = 5)
    historicData    = kite.historical_data(instrument_token=BNInstrumentToken, from_date=from_date, to_date=to_date, interval='5minute')
    run(historicData)
    time.sleep(300) # sleep for 5 minute until next candle formed
