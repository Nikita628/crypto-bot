import pandas as pd
import pandas_ta

def add_gmma(df: pd.DataFrame):
    short_emas = [3, 5, 8, 10, 12, 15]
    long_emas = [30, 35, 40, 45, 50, 60]
    for ema in short_emas:
        df[f'short_ema_{ema}'] = pandas_ta.ema(close=df['close'], length=ema)
    for ema in long_emas:
        df[f'long_ema_{ema}'] = pandas_ta.ema(close=df['close'], length=ema)

def add_stoch_osc(df: pd.DataFrame, k, d, smooth, name, fillna=False):
    stoch = pandas_ta.stoch(df['high'], df['low'], df['close'], k=k, d=d, fillna=fillna, smooth_k=smooth)
    df[f'stoch_{name}'] = stoch[f'STOCHd_{k}_{d}_{smooth}']

    # n = 20  # Lookback period for original %K
    # p = 8   # Period for smoothing %K
    # m = 3   # Period for %D
    # # Original %K Calculation
    # df['Low_n'] = df['low'].rolling(window=n).min()
    # df['High_n'] = df['high'].rolling(window=n).max()
    # df['%K'] = ((df['close'] - df['Low_n']) / (df['High_n'] - df['Low_n'])) * 100
    # # Smoothed %K Calculation
    # df['%K_smoothed'] = df['%K'].rolling(window=p).mean()
    # # %D Calculation using Smoothed %K
    # df['%D'] = df['%K_smoothed'].rolling(window=m).mean()

def add_rsi(df: pd.DataFrame, window=7):
    df['rsi'] = pandas_ta.rsi(close=df['close'], length=window)

def add_ema(name: str, df: pd.DataFrame, length=7):
    df[name] = pandas_ta.ema(close=df['close'], length=length)

def add_sma(name: str, source_column: str, df: pd.DataFrame):
    df[name] = df[source_column].rolling(window=9).mean()

def is_upward(source_column: str, df: pd.DataFrame) -> bool:
    return df[source_column].iloc[-1] > df[source_column].iloc[-2]

def is_above(source_column: str, value: float, df: pd.DataFrame) -> bool:
    return df[source_column].iloc[-1] > value

# TODO: move the above functions into the mixin below
class PandasMixin:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def is_upward(self, source_column: str) -> bool:
        return df[source_column].iloc[-1] > df[source_column].iloc[-2] 
    
    def is_above(self, source_column: str, value: float) -> bool:
        return df[source_column].iloc[-1] > value
    
    # add_rsi:
    # add_sma:
    # ...

# somewhere in code far far away ....  Using the custom accessor
df = pd.DataFrame()
df.custom.is_upward("volume")

