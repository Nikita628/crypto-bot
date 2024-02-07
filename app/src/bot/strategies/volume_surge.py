from bot.models.kline import KLine
from bot.models.trade import (
    ExitReason,
    Trade, 
    TradeDirection,
    get_current_profit_percentage, 
    is_trailing_stop,
    is_greedy_profit_reached,
    is_atr_stop_loss,
)
from bot.exchange.binance import BinanceInterval
from typing import Optional
from strategies.base import Base

_LOOCKBACK = 501 # precisely 501 is required to properly calculate 200 ema

class VolumeSurge(Base):
    def __init__(
            self, 
            timeframe: BinanceInterval = BinanceInterval.day, 
            name = 'volume_surge',
            hold_period_hours:Optional[float] = None,
            hold_exit_reason:Optional[set] = set(),
            trailing_stop_percentage:Optional[float] = None,
            greedy_profit_percentage:Optional[float] = None,
            hard_stop_loss_percentage:Optional[float] = None,
            pvt_surge_percentage:float = 5,
            pvt_range_percentage:float = 3,
            pvt_range_loockback:int = 7,
        ):
        super().__init__(timeframe, _LOOCKBACK, name, hold_period_hours, hold_exit_reason)
        self.trailing_stop_percentage = trailing_stop_percentage
        self.greedy_profit_percentage = greedy_profit_percentage
        self.hard_stop_loss_percentage = hard_stop_loss_percentage
        self.pvt_surge_percentage = pvt_surge_percentage
        self.pvt_range_percentage = pvt_range_percentage
        self.pvt_range_loockback = pvt_range_loockback

    def determine_trade_direction(self, kline: KLine, symbol: str) -> Optional[TradeDirection]:
        kline.add_pvt()
        kline.add_mfi()
        kline.add_rsi()
        kline.add_atr()

        current_atr_value = kline.df[KLine.Col.atr].iloc[-1]
        atr_percentage = current_atr_value / kline.get_running_price() * 100

        if (self.greedy_profit_percentage 
            and self.greedy_profit_percentage > 0
            and atr_percentage <= self.greedy_profit_percentage):
            return None

        if self.is_long_entry(kline):
            return TradeDirection.long
        
        return None


    def determine_exit_reason(self, kline: KLine, trade: Trade) -> Optional[ExitReason]:
        reason = None

        kline.add_pvt()
        kline.add_mfi()
        kline.add_rsi()

        if trade.direction == TradeDirection.long.value and self.is_long_exit(kline):
            reason = ExitReason.long_exit
        elif is_atr_stop_loss(kline.get_running_price(), trade):
            reason = ExitReason.atr_stop_loss
        elif self.greedy_profit_percentage and is_greedy_profit_reached(
            kline.get_running_price(), 
            trade, 
            greedy_percentage=self.greedy_profit_percentage
        ):
            reason = ExitReason.greedy_percentage
        elif self.trailing_stop_percentage and is_trailing_stop(
            kline.get_running_price(), 
            trade, 
            self.trailing_stop_percentage
        ):
            reason = ExitReason.trailing_stop
        elif (self.hard_stop_loss_percentage 
              and get_current_profit_percentage(kline.get_running_price(), trade) < self.hard_stop_loss_percentage):
            reason = ExitReason.hard_stop_loss
            
        return reason


    def is_long_entry(self, kline: KLine):
        current_pvt = kline.df[KLine.Col.pvt].iloc[-1]
        previous_pvt = kline.df[KLine.Col.pvt].iloc[-2]
        is_pvt_surged_upward = current_pvt > previous_pvt and (
            abs((current_pvt - previous_pvt) / previous_pvt * 100) > self.pvt_surge_percentage
        )
        overbought_limit = 80
        oversold_limit = 30

        return all([
            # all previous pvt do not change significantly (i.e. pvt is flat on the chart)
            kline.is_ranging_within_percentage(
                KLine.Col.pvt, 
                self.pvt_range_loockback,
                self.pvt_range_percentage
            ),
            is_pvt_surged_upward,

            kline.is_upward(KLine.Col.rsi),
            kline.is_between(KLine.Col.rsi, oversold_limit, overbought_limit),

            kline.is_upward(KLine.Col.mfi),
            kline.is_between(KLine.Col.mfi, oversold_limit, overbought_limit),
        ])
    

    def is_long_exit(self, kline: KLine):
        return all([
            kline.is_downward(KLine.Col.mfi),
            kline.is_downward(KLine.Col.rsi),
            kline.is_downward(KLine.Col.pvt),
        ])
       
