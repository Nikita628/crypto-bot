import pandas as pd
import pandas_ta
from core import KLineShape

class DataFrameDecorator:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def is_long_gmma_upward(self):
        _is_long_gmma_upward = all(
            (self.df[f'long_ema_{ema}'].iloc[-1] > self.df[f'long_ema_{ema}'].iloc[-2]) 
            for ema in KLineShape.long_emas
        )

        is_long_gmma_separation = True
        for i in range(0, len(KLineShape.long_emas) - 1):
            if self.df[f'long_ema_{KLineShape.long_emas[i]}'].iloc[-1] <= self.df[f'long_ema_{KLineShape.long_emas[i + 1]}'].iloc[-1]:
                is_long_gmma_separation = False
                break

        return _is_long_gmma_upward and is_long_gmma_separation

    def is_short_gmma_upward(self):
        _is_short_gmma_upward = all(
            (self.df[f'short_ema_{ema}'].iloc[-1] > self.df[f'short_ema_{ema}'].iloc[-2]) 
            for ema in KLineShape.short_emas
        )

        is_short_gmma_separation = True
        for i in range(0, len(KLineShape.short_emas) - 1):
            if self.df[f'short_ema_{KLineShape.short_emas[i]}'].iloc[-1] <= self.df[f'short_ema_{KLineShape.short_emas[i + 1]}'].iloc[-1]:
                is_short_gmma_separation = False
                break

        return _is_short_gmma_upward and is_short_gmma_separation

    def is_long_gmma_downward(self):
        _is_long_gmma_downward = all(
            (self.df[f'long_ema_{ema}'].iloc[-1] < self.df[f'long_ema_{ema}'].iloc[-2]) 
            for ema in KLineShape.long_emas
        )

        is_long_gmma_separation = True
        for i in range(0, len(KLineShape.long_emas) - 1):
            if self.df[f'long_ema_{KLineShape.long_emas[i]}'].iloc[-1] >= self.df[f'long_ema_{KLineShape.long_emas[i + 1]}'].iloc[-1]:
                is_long_gmma_separation = False
                break

        return _is_long_gmma_downward and is_long_gmma_separation

    def is_short_gmma_downward(self):
        _is_short_gmma_downward = all(
            (self.df[f'short_ema_{ema}'].iloc[-1] < self.df[f'short_ema_{ema}'].iloc[-2]) 
            for ema in KLineShape.short_emas
        )

        is_short_gmma_separation = True
        for i in range(0, len(KLineShape.short_emas) - 1):
            if self.df[f'short_ema_{KLineShape.short_emas[i]}'].iloc[-1] >= self.df[f'short_ema_{KLineShape.short_emas[i + 1]}'].iloc[-1]:
                is_short_gmma_separation = False
                break

        return _is_short_gmma_downward and is_short_gmma_separation

    def add_gmma(self):
        for ema in KLineShape.short_emas:
            self.df[f'short_ema_{ema}'] = pandas_ta.ema(close=self.df[KLineShape.close], length=ema)
        for ema in KLineShape.long_emas:
            self.df[f'long_ema_{ema}'] = pandas_ta.ema(close=self.df[KLineShape.close], length=ema)

    def add_stoch(self, k, d, smooth, name, fillna=False):
        stoch = pandas_ta.stoch(
            self.df[KLineShape.high], 
            self.df[KLineShape.low], 
            self.df[KLineShape.close], 
            k=k, 
            d=d, 
            fillna=fillna, 
            smooth_k=smooth
        )
        self.df[name] = stoch[f'STOCHd_{k}_{d}_{smooth}']
        # n = 20  # Lookback period for original %K
        # p = 8   # Period for smoothing %K
        # m = 3   # Period for %D
        # # Original %K Calculation
        # self.df['Low_n'] = self.df['low'].rolling(window=n).min()
        # self.df['High_n'] = self.df['high'].rolling(window=n).max()
        # self.df['%K'] = ((self.df['close'] - self.df['Low_n']) / (self.df['High_n'] - self.df['Low_n'])) * 100
        # # Smoothed %K Calculation
        # self.df['%K_smoothed'] = self.df['%K'].rolling(window=p).mean()
        # # %D Calculation using Smoothed %K
        # self.df['%D'] = self.df['%K_smoothed'].rolling(window=m).mean()

    def add_rsi(self, name: str, window=7):
        self.df[name] = pandas_ta.rsi(close=self.df[KLineShape.close], length=window)

    def add_ema(self, name: str, length=7):
        self.df[name] = pandas_ta.ema(close=self.df[KLineShape.close], length=length)

    def add_pvt(self, name: str):
        self.df[name] = pandas_ta.pvt(close=self.df[KLineShape.close], volume=self.df[KLineShape.volume])

    def add_mfi(self, name: str, length=7):
        self.df[name] = pandas_ta.mfi(
            close=self.df[KLineShape.close], 
            high=self.df[KLineShape.high], 
            low=self.df[KLineShape.low], 
            volume=self.df[KLineShape.volume], length=length
        )

    def add_sma(self, name: str, source_column: str, length=7):
        self.df[name] = self.df[source_column].rolling(window=length).mean()

        
    def is_upward(self, source_column: str) -> bool:
        return self.df[source_column].iloc[-1] > self.df[source_column].iloc[-2] 
    
    def is_above(self, source_column: str, value: float) -> bool:
        return self.df[source_column].iloc[-1] > value
    
    def is_downward(self, source_column: str) -> bool:
        return self.df[source_column].iloc[-1] < self.df[source_column].iloc[-2] 
    
    def is_below(self, source_column: str, value: float) -> bool:
        return self.df[source_column].iloc[-1] < value
    

# somewhere in code far far away ....  Using the custom accessor
# self = pd.DataFrame()
# self.custom.is_upward("volume")

