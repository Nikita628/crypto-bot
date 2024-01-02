import requests
import pandas as pd
from enum import Enum
from bot.kline import KLine
from typing import List
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

class BinanceInterval(Enum):
    min1 = '1m'
    min5 = '5m'
    min15 = '15m'
    h1 = '1h'
    h4 = '4h'
    h12 = '12h'
    day = '1d'

_RATE_LIMIT_CODE = 429
class RateLimitException(Exception):
    def __init__(self, message="rate limit is broken"):
        self.message = message
        super().__init__(self.message)

_RETRY_COUNT = 80
_BACKOFF_FACTOR = 2
_STATUS_FORCELIST = [500, 502, 503, 504]
_REQUEST_TIMEOUT = 300

def get_kline(symbol: str, interval: BinanceInterval, lookback: int) -> KLine:
    url = 'https://api.binance.com/api/v3/klines'
    
    # Setup retry strategy
    retries = Retry(total=_RETRY_COUNT, backoff_factor=_BACKOFF_FACTOR, status_forcelist=_STATUS_FORCELIST)
    adapter = HTTPAdapter(max_retries=retries)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    params = {
        'symbol': symbol,
        'interval': interval.value,
        'limit': lookback
    }
    
    response = None
    try:
        response = http.get(url, params=params, timeout=_REQUEST_TIMEOUT)
    except Exception as e:
        print(f'error during request to binance API: {response}, {e}')
        raise e

    if response.status_code == _RATE_LIMIT_CODE:
        raise RateLimitException()

    data = response.json()

    df = pd.DataFrame(data, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 
                                     'close_time', 'quote_asset_volume', 'number_of_trades', 
                                     'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    
    for col in ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume']:
        df[col] = df[col].astype(float)
    
    return KLine(df)

def get_all_usdt_symbols() -> List[str]:
    url = 'https://api.binance.com/api/v3/exchangeInfo'

    # Setup retry strategy
    retries = Retry(total=_RETRY_COUNT, backoff_factor=_BACKOFF_FACTOR, status_forcelist=_STATUS_FORCELIST)
    adapter = HTTPAdapter(max_retries=retries)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    response = None
    try:
        response = http.get(url, timeout=_REQUEST_TIMEOUT)
    except Exception as e:
        print(f'error during request to binance API: {response}, {e}')
        raise e
    
    if response.status_code == _RATE_LIMIT_CODE:
        raise RateLimitException()
    
    data = response.json()

    usdt_pairs = []
    for pair in data['symbols']:
        if pair['symbol'].endswith('USDT') and pair['status'] == 'TRADING':
            usdt_pairs.append(pair['symbol'])
    
    return usdt_pairs
