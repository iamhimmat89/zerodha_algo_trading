# Algo Trading with Himmat
    # Strategy  - VWAP Crossover
    # Entry     - VWAP Crossover Above (Call), VWAP Crossover Below (Put)
    # Exit      - Set defined Stop Loss or Target

import datetime as dt
import pandas as pd
import pandas_ta as ta
import time

from configparser import ConfigParser
from kiteconnect import KiteConnect
# read config.ini
config          = ConfigParser()
config.read('config.ini')
# Zerodha_APP details section
api_key         = config.get('Zerodha_APP', 'api_Key')
api_secret      = config.get('Zerodha_APP', 'api_secret')
kite            = KiteConnect(api_key=api_key)
# print(kite.login_url()) # https://kite.zerodha.com/connect/login?api_key=*********&v=3
data            = kite.generate_session("erKTxgzTAUWlonoEUA1uuuE10f7gFGji", api_secret=api_secret)
access_token    = data["access_token"]
kite.set_access_token(access_token)

# initialize variables
is_long_trade       = False
is_short_trade      = False
vwap_period         = 20
option_symbol       = 'BANKNIFTY24131'
trade_quantity      = 15
future_symbol       = 'BANKNIFTY24FEBFUT'

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


def calculate_vwap(data):
    data["vwap_1"] = ta.vwap(data['high'], data['low'], data['close'], data['volume'], anchor=None, offset=None)
    return data


def process_data(data):
    global is_long_trade, is_short_trade
    
    df          = pd.DataFrame(data)
    df[0]       = pd.to_datetime(df['date'], unit='s')
    df.set_index(0, inplace=True)
    data        = calculate_vwap(df)

    # Get the latest VWAP and close price
    previous_vwap   = data['vwap_1'].iloc[-2]
    previous_close  = data['close'].iloc[-2]
    current_vwap    = data['vwap_1'].iloc[-1]
    current_close   = data['close'].iloc[-1]

    print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
          " -2 Candle : VWAP : "+str(previous_vwap)+" Close Price : "+str(previous_close))
    print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
          " -1 Candle : VWAP : "+str(current_vwap)+" Close Price : "+str(current_close))

    # Check for VWAP crossover above for Call Buy
    if previous_close < previous_vwap and current_close > current_vwap and not is_long_trade:
        print("Call Buy Entry : ")
        round_to_strike     = int(round(float(df['close'].iloc[-1]), -2)) # round closed price to nearest strike price
        call_symbol         = str(option_symbol)+str(round_to_strike)+'CE'
        orderId             = placeOrder(call_symbol, 'BUY')
        is_long_trade       = True

    # Check for VWAP crossover below for Put Buy
    elif previous_close > previous_vwap and current_close < current_vwap and not is_short_trade:
        print("Put Buy Entry : ")
        round_to_strike = int(round(float(df['close'].iloc[-1]), -2)) # round closed price to nearest strike price
        put_symbol      = str(option_symbol)+str(round_to_strike)+'PE'
        orderId         = placeOrder(put_symbol, 'BUY')
        is_short_trade  = True

    # SL & Target Logic
    # if is_long_trade:
         # logic to exit the call trade on SL or Target 
         # is_long_trade = False

    # SL & Target Logic
    # if is_short_trade:
         # logic to exit the Put trade on SL or Target 
         # is_short_trade = False

# Get Bank Nifty Future Instrument Token to Fetch Historical Data
instruments         = kite.instruments('NFO')
instrumentsDf       = pd.DataFrame(instruments)
bankNiftyDf         = instrumentsDf[instrumentsDf['tradingsymbol'] == future_symbol]
BNInstrumentToken   = bankNiftyDf['instrument_token'].iloc[0]

while True:
    to_date         = dt.datetime.now().date()
    from_date       = to_date - dt.timedelta(days = 5)
    historicData    = kite.historical_data(instrument_token=BNInstrumentToken, from_date=from_date, to_date=to_date, interval='5minute')
    process_data(historicData)
    time.sleep(300) # sleep for 5 minute until next candle formed
