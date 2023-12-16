from .base import Base
import pandas as pd

# Strategy description in comments ...
#
#

class DualMomentum(Base):
    def add_entry_tech_indicators(self, df: pd.DataFrame):
        # add_gmma(df)
                        # add_ema('ema_200', df, 200)
                        # add_rsi(df)
                        # add_sma(KLineShape.volume_sma, 'volume', df) # TODO: replace all strings to KLineShape
                        # add_stoch_osc(df, 5, 3, 2, 'short')
                        # add_stoch_osc(df, 20, 3, 8, 'long')
        pass


    def add_exit_tech_indicators(self, df: pd.DataFrame):
        # add_rsi(df)
                        # add_stoch_osc(df, 5, 3, 2, 'short')
                        # add_stoch_osc(df, 20, 3, 8, 'long')
        pass

    def is_long_entry(self, df: pd.DataFrame) -> bool:
        pass

    def is_long_exit(self, df: pd.DataFrame, deal: Deal) -> bool:
        pass

    def is_short_entry(self, df: pd.DataFrame) -> bool:
        pass

    def is_short_exit(self, df: pd.DataFrame, deal: Deal) -> bool:
        pass