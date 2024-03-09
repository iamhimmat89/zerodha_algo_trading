# Algo Trading with Himmat
    # Strategy  - 5 EMA (Power of Stocks) - 5 Min Candle
    # Entry     - Low of previous candle should not touch 5 ema and current candle price crosses below low of previous candle 
    # SL        - High of the candle
    # Target    - 2x of candle size

import datetime as dt
import pandas as pd
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
is_trade            = False
ema_period          = 5
banknifty_symbol    = 'NSE:NIFTY BANK'
option_symbol       = 'BANKNIFTY24207'
trade_quantity      = 15
stop_loss           = None
target              = None
put_symbol          = None 

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

def process_data():    
    # get ltp of bank nifty
    ltp = kite.ltp(banknifty_symbol)[banknifty_symbol]['last_price']

    print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
          " LTP : "+str(ltp)+" 5 EMA : "+str(candle_ema)+" High : "+str(candle_high)+" Low : "+str(candle_low))

    # check entry condition
    if candle_low > candle_ema and ltp < candle_low and not is_trade:
        stop_loss           = candle_high
        target              = candle_low - ((candle_high - candle_low) * 2)
        print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
              " Buy ATM Put Option. SL :: "+str(stop_loss)+", Target :: "+str(target))
        round_to_strike     = int(round(float(df['close'].iloc[-1]), -2)) # round closed price to nearest strike price
        put_symbol         = str(option_symbol)+str(round_to_strike)+'PE'
        orderId             = placeOrder(put_symbol, 'BUY')
        is_trade            = True

    # check for sl or target of traded call
    if is_trade:
        if ltp > stop_loss:
            print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
                " Stop Loss Hit: Crosses Above")
            orderId         = placeOrder(put_symbol, 'SELL')
            is_trade        = False
        if ltp < target:
            print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
                " Target Hit")
            orderId         = placeOrder(put_symbol, 'SELL')
            is_trade        = False


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
    df              = pd.DataFrame(historicData)
    df['ema']       = df['close'].ewm(span=ema_period, adjust=False).mean()
    candle_low      = df['low'].iloc[-1]
    candle_high     = df['high'].iloc[-1]
    candle_ema      = df['ema'].iloc[-1]
    print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
        " 5 EMA : "+str(candle_ema)+" High : "+str(candle_high)+" Low : "+str(candle_low))

    t_end           = time.time() + (5 * 60) # 5 mins until next candle formed    
    while time.time() < t_end:
        time.sleep(1)
        process_data()
    
    