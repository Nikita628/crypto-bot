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

RATE_LIMIT_CODE = 429
class RateLimitException(Exception):
    def __init__(self, message="rate limit is broken"):
        self.message = message
        super().__init__(self.message)


def get_kline(symbol: str, interval: BinanceInterval, lookback: int) -> KLine:
    url = 'https://api.binance.com/api/v3/klines'
    
    # Setup retry strategy
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    params = {
        'symbol': symbol,
        'interval': interval.value,
        'limit': lookback
    }
    
    response = http.get(url, params=params, timeout=60)

    if response.status_code == RATE_LIMIT_CODE:
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
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    response = http.get(url, timeout=60)

    if response.status_code == RATE_LIMIT_CODE:
        raise RateLimitException()
    
    data = response.json()

    usdt_pairs = []
    for pair in data['symbols']:
        if pair['symbol'].endswith('USDT') and pair['status'] == 'TRADING':
            usdt_pairs.append(pair['symbol'])
    
    return usdt_pairs
