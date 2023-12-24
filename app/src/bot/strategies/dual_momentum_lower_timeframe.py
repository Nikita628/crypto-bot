from strategies.base import Base
from bot.kline import KLine
from bot.trade import Trade, TradeDirection
from bot.binance import BinanceInterval
from typing import Optional

# Dual momentum on lower timeframes

# starting on 5 min
# exiting too early because stochs already down, but trend continues,
# too sensitive on 5 min.
# to prevent early exit, updated condition, so that stochs AND rsi should signal exit,
# instead of stochs OR rsi

LOOCKBACK = 501 # precisely 501 is required to properly calculate 200 ema

class DualMomentumLowerTimeframe(Base):
    def __init__(self):
        super().__init__(BinanceInterval.min_5, LOOCKBACK, 'dual_momentum_5_min')

    def determine_trade_direction(self, kline: KLine) -> Optional[TradeDirection]:
        kline.add_ema(KLine.Col.ema_200, 200)
        kline.add_gmma()
        kline.add_stoch(5, 3, 2, KLine.Col.stoch_short)
        kline.add_stoch(20, 3, 8, KLine.Col.stoch_long)
        kline.add_rsi(KLine.Col.rsi)

        if self.is_long_entry(kline):
            return TradeDirection.long
        elif self.is_short_entry(kline):
            return TradeDirection.short
        
        return None

    def determine_exit_reason(self, kline: KLine, deal: Trade) -> Optional[str]:
        kline.add_stoch(5, 3, 2, KLine.Col.stoch_short)
        kline.add_stoch(20, 3, 8, KLine.Col.stoch_long)
        kline.add_rsi(KLine.Col.rsi)
        
        reason = None
        if deal.direction == TradeDirection.long.value and self.is_long_exit(kline):
            reason = 'long exit'
        elif deal.direction == TradeDirection.short.value and self.is_short_exit(kline):
            reason = 'short exit'

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