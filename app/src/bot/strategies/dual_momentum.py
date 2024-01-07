from strategies.base import Base
from bot.kline import KLine
from bot.trade import (
    Trade, 
    TradeDirection, 
    is_trailing_stop,
    is_greedy_profit_reached,
    is_atr_stop_loss,
)
from bot.binance import BinanceInterval
from typing import Optional


_LOOCKBACK = 501 # precisely 501 is required to properly calculate 200 ema

class DualMomentum(Base):
    def __init__(
            self, 
            timeframe: BinanceInterval=BinanceInterval.day, 
            name='dual_momentum',
            trailing_stop_percentage:Optional[float] = None,
            greedy_profit_percentage:Optional[float] = None,
        ):
        super().__init__(timeframe, _LOOCKBACK, name)
        self.trailing_stop_percentage = trailing_stop_percentage
        self.greedy_profit_percentage = greedy_profit_percentage

    def determine_trade_direction(self, kline: KLine) -> Optional[TradeDirection]:
        kline.add_ema(KLine.Col.ema_200, 200)
        kline.add_gmma()
        kline.add_stoch(5, 3, 2, KLine.Col.stoch_short)
        kline.add_stoch(20, 3, 8, KLine.Col.stoch_long)
        kline.add_rsi()

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
        elif is_atr_stop_loss(kline.get_running_price(), trade):
            reason = 'ATR stop loss'
        elif self.greedy_profit_percentage and is_greedy_profit_reached(
            kline.get_running_price(), 
            trade, 
            greedy_percentage=self.greedy_profit_percentage
        ):
            reason = 'greedy percentage'
        elif self.trailing_stop_percentage and is_trailing_stop(
            kline.get_running_price(), 
            trade, 
            self.trailing_stop_percentage
        ):
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

            (kline.is_below(KLine.Col.stoch_long, 80)
             and kline.is_above(KLine.Col.stoch_long, 20)),

            (kline.is_below(KLine.Col.stoch_short, 80)
            and kline.is_above(KLine.Col.stoch_short, 20)),
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

            (kline.is_above(KLine.Col.stoch_long, 20)
             and kline.is_below(KLine.Col.stoch_long, 80)),

            (kline.is_above(KLine.Col.stoch_short, 20)
             and kline.is_below(KLine.Col.stoch_short, 80)),
        ])
    
    def is_long_exit(self, kline: KLine):
        return (
            all([
                kline.is_downward(KLine.Col.stoch_long),
                kline.is_downward(KLine.Col.stoch_short),
            ]) or all ([
                kline.is_below(KLine.Col.rsi, 50),
                kline.is_downward(KLine.Col.rsi),
            ])
        )

    def is_short_exit(self, kline: KLine):
        return (
            all([
                kline.is_upward(KLine.Col.stoch_long),
                kline.is_upward(KLine.Col.stoch_short),
            ]) or all ([
                kline.is_upward(KLine.Col.rsi),
                kline.is_above(KLine.Col.rsi, 50),
            ])
        )