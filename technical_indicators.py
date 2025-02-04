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

def add_200ema(df: pd.DataFrame):
    df['ema_200'] = pandas_ta.ema(close=df['close'], length=200)

def add_volume_sma(df: pd.DataFrame, window=7):
    df['volume_sma'] = df['volume'].rolling(window=window).mean()

def add_pvt(df: pd.DataFrame, length=1):
    df['pvt'] = pandas_ta.pvt(close=df['close'], volume=df['volume'], drift=length)

def add_mfi(df: pd.DataFrame, length=7):
    df['mfi'] = pandas_ta.mfi(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'], length=length)
