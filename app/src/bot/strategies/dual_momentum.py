from .base import Base
from ..technical_indicators import DataFrameDecorator
from ..deal import Deal, DealDirection
from ..core import KLineShape

# Pure dual momentum as described by the book

class DualMomentum(Base):
    def __init__(self):
        self.strategy = 'dual_momentum'

    def get_entry_direction(self, df: DataFrameDecorator) -> DealDirection or None:
        if self.is_long_entry(df):
            return DealDirection.long
        elif self.is_short_entry(df):
            return DealDirection.short
        
        return None

    def is_exit(self, df: DataFrameDecorator, deal: Deal) -> bool:
        return self.is_long_exit(df) or self.is_short_exit(df)

    def is_long_entry(df: DataFrameDecorator):
        df.add_ema(KLineShape.ema_200, 200)
        df.add_gmma()
        df.add_stoch(5, 3, 2, KLineShape.stoch_short)
        df.add_stoch(20, 3, 8, KLineShape.stoch_long)
        df.add_rsi(KLineShape.rsi)

        is_200ema_upward = df.is_upward(KLineShape.ema_200)
        is_long_gmma_above_200ema = df.df[f'long_ema_{60}'].iloc[-1] > df.df[KLineShape.ema_200].iloc[-1]
        is_short_term_GMMA_above_long_term_GMMA = df.df[f'short_ema_{15}'].iloc[-1] > df.df[f'long_ema_{30}'].iloc[-1]
      
        return all([
            is_200ema_upward, 

            is_long_gmma_above_200ema, 
            df.is_long_gmma_upward(),

            is_short_term_GMMA_above_long_term_GMMA,
            df.is_short_gmma_upward(),

            df.is_upward(KLineShape.stoch_short),
            df.is_upward(KLineShape.stoch_long),

            df.is_upward(KLineShape.rsi),
            df.is_above(KLineShape.rsi, 50),
        ])
    
    def is_short_entry(df: DataFrameDecorator):
        df.add_ema(KLineShape.ema_200, 200)
        df.add_gmma()
        df.add_stoch(5, 3, 2, KLineShape.stoch_short)
        df.add_stoch(20, 3, 8, KLineShape.stoch_long)
        df.add_rsi(KLineShape.rsi)
    
        is_long_gmma_below_200ema = df[f'long_ema_{60}'].iloc[-1] < df['ema_200'].iloc[-1]
        is_short_term_GMMA_below_long_term_GMMA = df[f'short_ema_{15}'].iloc[-1] < df[f'long_ema_{30}'].iloc[-1]

        return all([
            df.is_downward(KLineShape.ema_200), 

            is_long_gmma_below_200ema, 
            df.is_long_gmma_downward(),

            is_short_term_GMMA_below_long_term_GMMA,
            df.is_short_gmma_downward(),

            df.is_downward(KLineShape.stoch_short),
            df.is_downward(KLineShape.stoch_long),

            df.is_downward(KLineShape.rsi),
            df.is_below(KLineShape.rsi, 50),
        ])
    
    def is_long_exit(df: DataFrameDecorator):
        return (
            all([
                df.is_downward(KLineShape.stoch_long),
                df.is_downward(KLineShape.stoch_short),
            ]) or all([
                df.is_below(KLineShape.rsi, 50),
                df.is_downward(KLineShape.rsi),
            ])
        )

    def is_short_exit(df: DataFrameDecorator):
        return (
            all([
                df.is_upward(KLineShape.stoch_long),
                df.is_upward(KLineShape.stoch_short),
            ]) or all([
                df.is_upward(KLineShape.rsi),
                df.is_above(KLineShape.rsi, 50),
            ])
        )