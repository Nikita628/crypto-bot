import pandas as pd
import pandas_ta

class KLine:
    class Col:
        open = 'open'
        close = 'close'
        high = 'high'
        low = 'low'
        volume = 'volume'
        quote_asset_volume = 'quote_asset_volume'

        short_emas = [3, 5, 8, 10, 12, 15]
        long_emas = [30, 35, 40, 45, 50, 60]
        rsi = 'rsi'
        volume_sma = 'volume_sma'
        ema_200 = 'ema_200'
        pvt = 'pvt'
        mfi = 'mfi'
        stoch_long = 'stoch_long'
        stoch_short = 'stoch_short'

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def get_running_price(self) -> float:
        return self.df[KLine.Col.close].iloc[-1]
    
    def is_rsi_overbought(self, overbought_limit = 85) -> bool: 
        return self.is_above(KLine.Col.rsi, overbought_limit)
    
    def is_rsi_oversold(self, oversold_limit = 15) -> bool: 
        return self.is_below(KLine.Col.rsi, oversold_limit)
    
    def is_stoch_overbought(self, overbought_limit = 85) -> bool:
        return (
            self.is_above(KLine.Col.stoch_long, overbought_limit)
            or self.is_above(KLine.Col.stoch_short, overbought_limit)
        )
    
    def is_stoch_oversold(self, oversold_limit = 15) -> bool:
        return (
            self.is_below(KLine.Col.stoch_long, oversold_limit)
            or self.is_below(KLine.Col.stoch_short, oversold_limit)
        )
    
    def is_long_gmma_above_200ema(self): 
        return self.df[f'long_ema_{60}'].iloc[-1] > self.df[KLine.Col.ema_200].iloc[-1]
    
    def is_short_term_GMMA_above_long_term_GMMA(self):
        return self.df[f'short_ema_{15}'].iloc[-1] > self.df[f'long_ema_{30}'].iloc[-1]
    
    def is_long_gmma_below_200ema(self):
        return self.df[f'long_ema_{60}'].iloc[-1] < self.df[KLine.Col.ema_200].iloc[-1]
    
    def is_short_term_GMMA_below_long_term_GMMA(self): 
        return self.df[f'short_ema_{15}'].iloc[-1] < self.df[f'long_ema_{30}'].iloc[-1]

    def is_long_gmma_upward(self):
        _is_long_gmma_upward = all(
            (self.df[f'long_ema_{ema}'].iloc[-1] > self.df[f'long_ema_{ema}'].iloc[-2]) 
            for ema in KLine.Col.long_emas
        )

        is_long_gmma_separation = True
        for i in range(0, len(KLine.Col.long_emas) - 1):
            if self.df[f'long_ema_{KLine.Col.long_emas[i]}'].iloc[-1] <= self.df[f'long_ema_{KLine.Col.long_emas[i + 1]}'].iloc[-1]:
                is_long_gmma_separation = False
                break

        return _is_long_gmma_upward and is_long_gmma_separation

    def is_short_gmma_upward(self):
        _is_short_gmma_upward = all(
            (self.df[f'short_ema_{ema}'].iloc[-1] > self.df[f'short_ema_{ema}'].iloc[-2]) 
            for ema in KLine.Col.short_emas
        )

        is_short_gmma_separation = True
        for i in range(0, len(KLine.Col.short_emas) - 1):
            if self.df[f'short_ema_{KLine.Col.short_emas[i]}'].iloc[-1] <= self.df[f'short_ema_{KLine.Col.short_emas[i + 1]}'].iloc[-1]:
                is_short_gmma_separation = False
                break

        return _is_short_gmma_upward and is_short_gmma_separation

    def is_long_gmma_downward(self):
        _is_long_gmma_downward = all(
            (self.df[f'long_ema_{ema}'].iloc[-1] < self.df[f'long_ema_{ema}'].iloc[-2]) 
            for ema in KLine.Col.long_emas
        )

        is_long_gmma_separation = True
        for i in range(0, len(KLine.Col.long_emas) - 1):
            if self.df[f'long_ema_{KLine.Col.long_emas[i]}'].iloc[-1] >= self.df[f'long_ema_{KLine.Col.long_emas[i + 1]}'].iloc[-1]:
                is_long_gmma_separation = False
                break

        return _is_long_gmma_downward and is_long_gmma_separation

    def is_short_gmma_downward(self):
        _is_short_gmma_downward = all(
            (self.df[f'short_ema_{ema}'].iloc[-1] < self.df[f'short_ema_{ema}'].iloc[-2]) 
            for ema in KLine.Col.short_emas
        )

        is_short_gmma_separation = True
        for i in range(0, len(KLine.Col.short_emas) - 1):
            if self.df[f'short_ema_{KLine.Col.short_emas[i]}'].iloc[-1] >= self.df[f'short_ema_{KLine.Col.short_emas[i + 1]}'].iloc[-1]:
                is_short_gmma_separation = False
                break

        return _is_short_gmma_downward and is_short_gmma_separation

    def add_gmma(self):
        for ema in KLine.Col.short_emas:
            self.df[f'short_ema_{ema}'] = pandas_ta.ema(close=self.df[KLine.Col.close], length=ema)
        for ema in KLine.Col.long_emas:
            self.df[f'long_ema_{ema}'] = pandas_ta.ema(close=self.df[KLine.Col.close], length=ema)

    def add_stoch(self, k, d, smooth, name, fillna=False):
        stoch = pandas_ta.stoch(
            self.df[KLine.Col.high], 
            self.df[KLine.Col.low], 
            self.df[KLine.Col.close], 
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
        self.df[name] = pandas_ta.rsi(close=self.df[KLine.Col.close], length=window)

    def add_ema(self, name: str, length=7):
        self.df[name] = pandas_ta.ema(close=self.df[KLine.Col.close], length=length)

    def add_pvt(self, name: str):
        self.df[name] = pandas_ta.pvt(close=self.df[KLine.Col.close], volume=self.df[KLine.Col.volume])

    def add_mfi(self, name: str, length=7):
        self.df[name] = pandas_ta.mfi(
            close=self.df[KLine.Col.close], 
            high=self.df[KLine.Col.high], 
            low=self.df[KLine.Col.low], 
            volume=self.df[KLine.Col.volume], length=length
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
    