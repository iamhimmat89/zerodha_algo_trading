from configparser import ConfigParser
from kiteconnect import KiteConnect

# read config.ini
config = ConfigParser()
config.read('config.ini')

# Zerodha_APP details section
api_key         = config.get('Zerodha_APP', 'api_Key')
api_secret      = config.get('Zerodha_APP', 'api_secret')

kite = KiteConnect(api_key=api_key)
# print(kite.login_url()) 
# https://kite.zerodha.com/connect/login?api_key=*********&v=3

data = kite.generate_session("erKTxgzTAUWlonoEUA1uuuE10f7gFGji", api_secret=api_secret)
access_token = data["access_token"]
print('access token ', access_token)

kite.set_access_token(access_token)

