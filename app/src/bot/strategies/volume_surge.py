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
from strategies.base import Base

LOOCKBACK = 501 # precisely 501 is required to properly calculate 200 ema
PVT_SURGE_PERCENTAGE = 4

class VolumeSurge(Base):
    def __init__(
            self, 
            timeframe: BinanceInterval = BinanceInterval.day, 
            name = 'volume_surge',
            trailing_stop_percentage:Optional[float] = None,
            greedy_profit_percentage:Optional[float] = None,
        ):
        super().__init__(timeframe, LOOCKBACK, name)
        self.trailing_stop_percentage = trailing_stop_percentage
        self.greedy_profit_percentage = greedy_profit_percentage


    def determine_trade_direction(self, kline: KLine) -> Optional[TradeDirection]:
        kline.add_pvt()
        kline.add_mfi()

        if self.is_long_entry(kline):
            return TradeDirection.long
        
        return None


    def determine_exit_reason(self, kline: KLine, trade: Trade) -> Optional[str]:
        reason = None

        kline.add_pvt()
        kline.add_mfi()

        if trade.direction == TradeDirection.long.value and self.is_long_exit(kline):
            reason = 'long exit'
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
        current_pvt = kline.df[KLine.Col.pvt].iloc[-1]
        previous_pvt = kline.df[KLine.Col.pvt].iloc[-2]
        is_pvt_surged_upward = current_pvt > previous_pvt and (
            (current_pvt - previous_pvt) / previous_pvt * 100 > PVT_SURGE_PERCENTAGE
        )

        return all([
            # all previous pvt do not change significantly (i.e. pvt is flat on the chart)
            kline.is_ranging_within_percentage(KLine.Col.pvt, -8, -1, 2),

            is_pvt_surged_upward,

            kline.is_upward(KLine.Col.mfi),
            kline.is_below(KLine.Col.mfi, 80),
        ])
    

    def is_long_exit(self, kline: KLine):
        return all([
            kline.is_downward(KLine.Col.mfi),
            kline.is_downward(KLine.Col.pvt)
        ])
       
