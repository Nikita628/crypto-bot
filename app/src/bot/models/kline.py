import pandas as pd
import pandas_ta
import numpy as np
from models.trade import TradeDirection

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
        stoch_long_d = 'stoch_long_d'
        stoch_short_d = 'stoch_short_d'
        stoch_long_k = 'stoch_long_k'
        stoch_short_k = 'stoch_short_k'
        atr = 'atr'

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def get_running_price(self) -> float:
        return self.df[KLine.Col.close].iloc[-1]
    
    def is_rsi_overbought(self, overbought_limit = 80) -> bool: 
        return self.is_above(KLine.Col.rsi, overbought_limit)
    
    def is_rsi_oversold(self, oversold_limit = 20) -> bool: 
        return self.is_below(KLine.Col.rsi, oversold_limit)
    
    def is_stoch_overbought(self, overbought_limit = 80) -> bool:
        return (
            self.is_above(KLine.Col.stoch_long_d, overbought_limit)
            or self.is_above(KLine.Col.stoch_short_d, overbought_limit)
        )
    
    def is_stoch_oversold(self, oversold_limit = 20) -> bool:
        return (
            self.is_below(KLine.Col.stoch_long_d, oversold_limit)
            or self.is_below(KLine.Col.stoch_short_d, oversold_limit)
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


    def add_stoch(self, k, d, smooth, name_d='stoch_d', name_k='stoch_k'):
        low_min = self.df[KLine.Col.low].rolling(window=k).min()
        high_max = self.df[KLine.Col.high].rolling(window=k).max()
        self.df['%K_raw'] = ((self.df[KLine.Col.close] - low_min) / (high_max - low_min)) * 100
        self.df[name_k] = self.df['%K_raw'].rolling(window=d).mean()
        self.df[name_d] = self.df[name_k].rolling(window=smooth).mean()


    def add_rsi(self, name: str='rsi', window=7):
        self.df[name] = pandas_ta.rsi(close=self.df[KLine.Col.close], length=window)


    def add_ema(self, name: str='ema', length=7):
        self.df[name] = pandas_ta.ema(close=self.df[KLine.Col.close], length=length)


    def add_pvt(self, name: str='pvt'):
        self.df[name] = pandas_ta.pvt(close=self.df[KLine.Col.close], volume=self.df[KLine.Col.volume])


    def add_atr(self, name: str='atr', length = 7):
        self.df[name] = pandas_ta.atr(
            high=self.df[KLine.Col.high],
            low=self.df[KLine.Col.low],
            close=self.df[KLine.Col.close],
            length=length,
        )

    def add_mfi(self, name: str='mfi', length=7):
        self.df[name] = pandas_ta.mfi(
            close=self.df[KLine.Col.close], 
            high=self.df[KLine.Col.high], 
            low=self.df[KLine.Col.low], 
            volume=self.df[KLine.Col.volume], length=length
        )

    def add_sma(self, name: str='sma', source_column: str='close', length=7):
        self.df[name] = self.df[source_column].rolling(window=length).mean()

        
    def is_upward(self, source_column: str, lookback = 1) -> bool:
        if (lookback < 1):
            raise Exception('loockback must be >= 1')
        
        for i in range(0, lookback):
            if self.df[source_column].iloc[-1 - i] <= self.df[source_column].iloc[-2 - i]:
                return False
            
        return True
    
    def is_above(self, source_column: str, value: float) -> bool:
        return self.df[source_column].iloc[-1] > value
    
    def is_downward(self, source_column: str, lookback = 1) -> bool:
        if (lookback < 1):
            raise Exception('loockback must be >= 1')
        
        for i in range(0, lookback):
            if self.df[source_column].iloc[-1 - i] >= self.df[source_column].iloc[-2 - i]:
                return False
            
        return True
    
    def is_below(self, source_column: str, value: float) -> bool:
        return self.df[source_column].iloc[-1] < value
    
    def is_between(self, source_column: str, min: float, max: float) -> bool:
        return self.is_below(source_column, max) and self.is_above(source_column, min)
    
    def is_ranging_within_percentage(self, source_column: str, loockback: int = 7, range_percentage: float = 1):
        values = self.df[source_column].iloc[-(loockback + 1):-1]

        for i in values:
            for j in values:
                if i != j and abs((i - j) / i * 100) > range_percentage:
                    return False

        return True
    
    def is_min_slope_diff(self, source_column: str, min_diff: float = 0, lookback = 1) -> bool:
        for i in range(0, lookback):
            if abs(self.df[source_column].iloc[-1 - i] - self.df[source_column].iloc[-2 - i]) < min_diff:
                return False
            
        return True
    
    
    def is_price_action_not_mixing_with_gmma(self, direction: TradeDirection) -> bool:
        current_low = self.df[KLine.Col.low].iloc[-1]
        current_high = self.df[KLine.Col.high].iloc[-1]
        current_open = self.df[KLine.Col.open].iloc[-1]
        current_close = self.df[KLine.Col.close].iloc[-1]
        current_gmma_30 = self.df[f'long_ema_{30}'].iloc[-1]

        if direction.value == TradeDirection.long.value:
            return (current_open > current_gmma_30 
                    and current_low > current_gmma_30
                    and current_close > current_gmma_30)
        else:
            return (current_high < current_gmma_30
                    and current_open < current_gmma_30
                    and current_close < current_gmma_30)
        

    def add_slope(self, source_column: str):
        self.df[f'slope_{source_column}'] = self.df[source_column].diff()

    def calc_volatility(self, loockback: int = 1) -> float:
        period = self.df.tail(loockback).copy()
        period.loc[:, 'log_return'] = np.log(period[KLine.Col.close] / period[KLine.Col.close].shift(1))
        std = period['log_return'].std()
        return round(std * 100, 2)
    

    def calc_ranging_percentage(self, source_column: str, loockback: int = 7) -> float:
        values = self.df[source_column].iloc[-(loockback + 1):-1]
        min = values.min()
        max = values.max()
        range = max - min
        percentage_range = abs(range / min) * 100
        return percentage_range
    

    def get_max(self, source_column: str, loockback: int = 7) -> float:
        values = self.df[source_column].iloc[-(loockback + 1):-1]
        return values.max()
