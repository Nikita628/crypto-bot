from bot.models.kline import KLine
from bot.models.trade import (
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

class VolumeSurgeCustomized(Base):
    def __init__(
            self, 
            timeframe: BinanceInterval = BinanceInterval.day, 
            name = 'volume_surge',
            hold_period_hours:Optional[float] = None,
            hold_exit_reason:Optional[set] = set(),
            trailing_stop_percentage:Optional[float] = None,
            greedy_profit_percentage:Optional[float] = None,
            hard_stop_loss_percentage:Optional[float] = None,
            pvt_surge_multiplier:float = 4,
            pvt_range_loockback:int = 7,
        ):
        super().__init__(timeframe, _LOOCKBACK, name, hold_period_hours, hold_exit_reason)
        self.trailing_stop_percentage = trailing_stop_percentage
        self.greedy_profit_percentage = greedy_profit_percentage
        self.hard_stop_loss_percentage = hard_stop_loss_percentage
        self.pvt_surge_multiplier = pvt_surge_multiplier
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


    def determine_exit_reason(self, kline: KLine, trade: Trade) -> Optional[str]:
        reason = None

        kline.add_pvt()
        kline.add_mfi()
        kline.add_rsi()

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
        elif (self.hard_stop_loss_percentage 
              and get_current_profit_percentage(kline.get_running_price(), trade) < self.hard_stop_loss_percentage):
            reason = 'hard stop loss'
            
        return reason


    def is_long_entry(self, kline: KLine):
        current_pvt = kline.df[KLine.Col.pvt].iloc[-1]
        percentage_range = kline.calc_ranging_percentage(KLine.Col.pvt, self.pvt_range_loockback)
        max_pvt = kline.get_max(KLine.Col.pvt, self.pvt_range_loockback)
        pvt_surged_percentage = abs(current_pvt - max_pvt) / max_pvt * 100
        
        overbought_limit = 80
        oversold_limit = 30

        is_long = all([
            current_pvt > max_pvt,
            pvt_surged_percentage >= percentage_range * self.pvt_surge_multiplier,

            kline.is_upward(KLine.Col.rsi),
            kline.is_between(KLine.Col.rsi, oversold_limit, overbought_limit),

            kline.is_upward(KLine.Col.mfi),
            kline.is_between(KLine.Col.mfi, oversold_limit, overbought_limit),
        ])


        if is_long:
            print(f'current_pvt: {current_pvt}, percentage_range: {percentage_range}, max_pvt: {max_pvt}, pvt_surged_pct: {pvt_surged_percentage}')

        return is_long
    

    def is_long_exit(self, kline: KLine):
        return all([
            kline.is_downward(KLine.Col.mfi),
            kline.is_downward(KLine.Col.rsi),
            kline.is_downward(KLine.Col.pvt),
        ])
       
