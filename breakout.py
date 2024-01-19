# Algo Trading with Himmat
    # Strategy  - Intraday 5 min Breakout 
    # Entry     - Breakout Above or Below 5 min Candle
    # SL        - Cross back opposite side of the candle
    # Target    - 2x of 5 min candle size

import datetime as dt
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

banknifty_symbol = 'NSE:NIFTY BANK'
print(kite.ltp('NSE:NIFTY BANK'))
print(kite.quote('NSE:NIFTY BANK'))

# get first 5 mins candle high and low price of bank nifty
while True:
	time.sleep(1)
	if dt.datetime.now().time() > dt.time(9,20):
		bankNifty_quote = kite.quote(banknifty_symbol)[banknifty_symbol]
		high_price      = bankNifty_quote['ohlc']['high']
		low_price       = bankNifty_quote['ohlc']['low']
		print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
          " high :: "+str(high_price)+" low :: "+str(low_price))
		break
		

# initialize variables
is_break_high           = False
is_break_low            = False
break_high_trade        = None
break_low_trade         = None
stop_loss               = None
target                  = None
trade_quantity          = 15 # change as per lots
option_symbol_prestring = 'BANKNIFTY24110' # need to change for every expiry, you can keep this in config file

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

while True:
	time.sleep(1)
	ltp = kite.ltp(banknifty_symbol)[banknifty_symbol]['last_price']
	print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
          " ltp :: "+str(ltp)+" high :: "+str(high_price)+" low :: "+str(low_price))
    # check for buy signal (cross above high)
	if ltp > high_price and not is_break_high and break_high_trade == None:
		stop_loss           = low_price
		target              = high_price + ((high_price - low_price) * 2)
		print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
              " Buy ATM Call Option (Breakout Above). SL :: "+str(stop_loss)+", Target :: "+str(target))
		round_to_strike     = int(round(float(ltp), -2)) # round ltp to nearest strike price
		call_symbol         = str(option_symbol_prestring)+str(round_to_strike)+'CE'
		orderId             = placeOrder(call_symbol, 'BUY')
		break_high_trade    = 1
		is_break_high       = True
		
    # check for sell signal (cross below low)
	if ltp < low_price and not is_break_low and break_low_trade == None:
		stop_loss           = high_price
		target              = low_price - ((high_price - low_price) * 2)
		print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
                " Buy ATM Call Option (Breakout Above). SL :: "+str(stop_loss)+", Target :: "+str(target))
		round_to_strike     = int(round(float(ltp), -2)) # round ltp to nearest strike price
		put_symbol          = str(option_symbol_prestring)+str(round_to_strike)+'PE'
		orderId             = placeOrder(put_symbol, 'BUY')
		break_low_trade     = 1
		is_break_low        = True
		
		
    # check for sl or target of traded buy / call 
	if is_break_high:
		if ltp < stop_loss:
			print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
                " Stop Loss Hit: Crosses Below")
			orderId         = placeOrder(call_symbol, 'SELL')
			is_break_high   = False
		if ltp > target:
			print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
                " Target Hit")
			orderId         = placeOrder(call_symbol, 'SELL')
			is_break_high   = False
		
    # check for sl or target of traded sell / put 
	if is_break_low:
		if ltp > stop_loss:
			print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
              " Stop Loss Hit: Crosses Above")
			orderId         = placeOrder(put_symbol, 'SELL')
			is_break_low    = False
		if ltp < target:
			print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
              " Target Hit")
			orderId         = placeOrder(put_symbol, 'SELL')
			is_break_low    = False
