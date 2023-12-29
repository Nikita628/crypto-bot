from bot.kline import KLine
from bot.trade import Trade, TradeDirection, is_trailing_stop
from bot.binance import BinanceInterval
from typing import Optional
from strategies.base import Base

LOOCKBACK = 501 # precisely 501 is required to properly calculate 200 ema

# customized dual momentum

# additional check if rsi is overbought/oversold

# additional check of volume sma

# additional check of mfi

# additional check on stochastics - they should both be going
# in one direction, and not overbought/oversold

class DualMomentumCustomized(Base):
    def __init__(
            self, 
            timeframe: BinanceInterval=BinanceInterval.day, 
            name='dual_momentum_customized',
            is_trailing_stop_enabled=False,
        ):
        super().__init__(timeframe, LOOCKBACK, name)
        self.is_trailing_stop_enabled = is_trailing_stop_enabled

    def determine_trade_direction(self, kline: KLine) -> Optional[TradeDirection]:
        kline.add_ema(KLine.Col.ema_200, 200)
        kline.add_gmma()
        kline.add_stoch(5, 3, 2, KLine.Col.stoch_short)
        kline.add_stoch(20, 3, 8, KLine.Col.stoch_long)
        kline.add_rsi()
        kline.add_sma(KLine.Col.volume_sma, KLine.Col.volume)
        kline.add_mfi()

        if self.is_long_entry(kline):
            return TradeDirection.long
        elif self.is_short_entry(kline):
            return TradeDirection.short
        
        return None

    def determine_exit_reason(self, kline: KLine, trade: Trade) -> Optional[str]:
        kline.add_stoch(5, 3, 2, KLine.Col.stoch_short)
        kline.add_stoch(20, 3, 8, KLine.Col.stoch_long)
        kline.add_rsi()

        reason = None
        if trade.direction == TradeDirection.long.value and self.is_long_exit(kline):
            reason = 'long exit'
        elif trade.direction == TradeDirection.short.value and self.is_short_exit(kline):
            reason = 'short exit'
        elif self.is_trailing_stop_enabled and is_trailing_stop(kline.get_running_price(), trade):
            reason = 'trailing stop'
            
        return reason

    def is_long_entry(self, kline: KLine):      
        return all([
            kline.is_upward(KLine.Col.ema_200), 

            kline.is_long_gmma_above_200ema(), 
            kline.is_long_gmma_upward(),

            kline.is_short_term_GMMA_above_long_term_GMMA(),
            kline.is_short_gmma_upward(),

            kline.is_upward(KLine.Col.stoch_short),
            kline.is_upward(KLine.Col.stoch_long),

            kline.is_upward(KLine.Col.rsi),
            kline.is_above(KLine.Col.rsi, 50),

            not kline.is_rsi_overbought(),
            not kline.is_above(KLine.Col.stoch_long, 80),
            not kline.is_above(KLine.Col.stoch_short, 60),

            kline.is_upward(KLine.Col.volume_sma),

            kline.is_upward(KLine.Col.mfi),
            not kline.is_above(KLine.Col.mfi, 80),
        ])
    
    
    def is_short_entry(self, kline: KLine):
        return all([
            kline.is_downward(KLine.Col.ema_200), 

            kline.is_long_gmma_below_200ema(), 
            kline.is_long_gmma_downward(),

            kline.is_short_term_GMMA_below_long_term_GMMA(),
            kline.is_short_gmma_downward(),

            kline.is_downward(KLine.Col.stoch_short),
            kline.is_downward(KLine.Col.stoch_long),

            kline.is_downward(KLine.Col.rsi),
            kline.is_below(KLine.Col.rsi, 50),

            not kline.is_rsi_oversold(),
            not kline.is_below(KLine.Col.stoch_long, 20),
            not kline.is_below(KLine.Col.stoch_short, 40),

            kline.is_upward(KLine.Col.volume_sma),

            kline.is_downward(KLine.Col.mfi),
            not kline.is_below(KLine.Col.mfi, 20),
        ])
    
    def is_long_exit(self, kline: KLine):
        return (
            all([
                kline.is_downward(KLine.Col.stoch_long),
                kline.is_downward(KLine.Col.stoch_short),
                kline.is_below(KLine.Col.rsi, 50),
                kline.is_downward(KLine.Col.rsi),
            ]) 
        )

    def is_short_exit(self, kline: KLine):
        return (
            all([
                kline.is_upward(KLine.Col.stoch_long),
                kline.is_upward(KLine.Col.stoch_short),
                kline.is_upward(KLine.Col.rsi),
                kline.is_above(KLine.Col.rsi, 50),
            ]) 
        )