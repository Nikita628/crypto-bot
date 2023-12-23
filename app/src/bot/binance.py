import requests
import pandas as pd
from enum import Enum
from app.src.bot.kline import KLine
from typing import List

class BinanceInterval(Enum):
    day = '1d'
    min_5 = '5m'

def get_kline(symbol: str, interval: BinanceInterval, lookback: int) -> KLine:
    url = f'https://api.binance.com/api/v3/uiKlines'
    params = {
        'symbol': symbol,
        'interval': interval.value,
        'limit': lookback
    }
    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(data, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 
                                     'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 
                                     'taker_buy_quote_asset_volume', 'ignore'])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

    for col in ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume']:
        df[col] = df[col].astype(float)

    return KLine(df)

def get_all_usdt_symbols() -> List[str]:
    url = 'https://api.binance.com/api/v3/exchangeInfo'
    response = requests.get(url)
    data = response.json()

    usdt_pairs = []
    for pair in data['symbols']:
        if pair['symbol'].endswith('USDT') and pair['status'] == 'TRADING':
            usdt_pairs.append(pair['symbol'])
    
    return usdt_pairs