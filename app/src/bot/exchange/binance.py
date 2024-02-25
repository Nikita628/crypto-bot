import requests
import pandas as pd
from enum import Enum
from bot.models.kline import KLine
from typing import List
import time
import json
import os

class BinanceInterval(Enum):
    min1 = '1m'
    min5 = '5m'
    min15 = '15m'
    h1 = '1h'
    h4 = '4h'
    h12 = '12h'
    day = '1d'
    week = '1w'

_RATE_LIMIT_CODE = 429
class RateLimitException(Exception):
    def __init__(self, message="rate limit is broken"):
        self.message = message
        super().__init__(self.message)

_RETRY_COUNT = 30
_BACKOFF_FACTOR = 1
_REQUEST_TIMEOUT = 30
_USDT_SYMBOLS: List[str] = []

def get_kline(symbol: str, interval: BinanceInterval, lookback: int) -> KLine:
    url = 'https://api.binance.com/api/v3/klines'
    params = {
        'symbol': symbol,
        'interval': interval.value,
        'limit': lookback
    }

    response = None
    for attempt in range(_RETRY_COUNT):
        try:
            response = requests.get(url, params=params, timeout=_REQUEST_TIMEOUT)
            break
        except Exception as e:
            if (attempt < _RETRY_COUNT - 1):
                delay_between_attempts = _BACKOFF_FACTOR * attempt
                time.sleep(delay_between_attempts)

    if not response:
        raise Exception('failed to get response')
    
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
    if len(_USDT_SYMBOLS) > 0:
        return _USDT_SYMBOLS
    
    url = 'https://api.binance.com/api/v3/exchangeInfo'

    response = None
    for attempt in range(_RETRY_COUNT):
        try:
            response = requests.get(url, timeout=_REQUEST_TIMEOUT)
            break
        except Exception as e:
            if (attempt < _RETRY_COUNT - 1):
                delay_between_attempts = _BACKOFF_FACTOR * attempt
                time.sleep(delay_between_attempts)
    
    if not response:
        raise Exception('failed to get response')
    
    if response.status_code == _RATE_LIMIT_CODE:
        raise RateLimitException()
    
    data = response.json()

    usdt_pairs = []
    for pair in data['symbols']:
        if pair['symbol'].endswith('USDT') and pair['status'] == 'TRADING':
            usdt_pairs.append(pair['symbol'])
    
    return usdt_pairs

def cache_usdt_symbols_list():
    global _USDT_SYMBOLS
    file_path = 'tradable_symbols.json'

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, 'r') as file:
            _USDT_SYMBOLS = json.load(file)
    else:
        _USDT_SYMBOLS = _filter_out_dangerous_symbols(get_all_usdt_symbols())
        with open(file_path, 'w') as file:
            json.dump(_USDT_SYMBOLS, file)


def _filter_out_dangerous_symbols(all_usdt_symbols: List[str]) -> List[str]:
    # in this context 'dangerous' means having tags 'Monitoring' or 'Seed'
    # when these tags are assigned by Binance, and when these tags are present
    # it means that price of the currency is highly volatile, or
    # it can be delisted soon etc.
    filtered_symbols: List[str] = []

    for symbol in all_usdt_symbols:
        tags = _get_symbol_tags(symbol)
        if 'Monitoring' not in tags and 'Seed' not in tags:
            filtered_symbols.append(symbol)
        time.sleep(1)

    return filtered_symbols


def _get_symbol_tags(symbol: str) -> List[str]:
    url = f'https://www.binance.com/bapi/asset/v2/public/asset-service/product/get-product-by-symbol?symbol={symbol}'

    response = None
    for attempt in range(_RETRY_COUNT):
        try:
            response = requests.get(url, timeout=_REQUEST_TIMEOUT)
            break
        except Exception as e:
            if (attempt < _RETRY_COUNT - 1):
                delay_between_attempts = _BACKOFF_FACTOR * attempt
                time.sleep(delay_between_attempts)
    
    if not response:
        raise Exception('failed to get response')
    
    if response.status_code == _RATE_LIMIT_CODE:
        raise RateLimitException()
    
    data = response.json()

    return data['data']['tags']