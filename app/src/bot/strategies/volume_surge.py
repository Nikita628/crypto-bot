from bot.kline import KLine
from bot.trade import Trade, TradeDirection, is_trailing_stop
from bot.binance import BinanceInterval
from typing import Optional
from strategies.base import Base

LOOCKBACK = 501 # precisely 501 is required to properly calculate 200 ema
PVT_SURGE_PERCENTAGE = 5

class VolumeSurge(Base):
    def __init__(
            self, 
            timeframe: BinanceInterval=BinanceInterval.day, 
            name='volume_surge',
        ):
        super().__init__(timeframe, LOOCKBACK, name)

    def determine_trade_direction(self, kline: KLine) -> Optional[TradeDirection]:
        kline.add_pvt()
        kline.add_mfi()

        if self.is_long_entry(kline):
            return TradeDirection.long
        
        return None

    def determine_exit_reason(self, kline: KLine, trade: Trade) -> Optional[str]:
        reason = None
        if is_trailing_stop(kline.get_running_price(), trade):
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
            kline.is_change_within_percentage(KLine.Col.pvt, -8, -1, 2),

            is_pvt_surged_upward,

            kline.is_upward(KLine.Col.mfi),
        ])
       
