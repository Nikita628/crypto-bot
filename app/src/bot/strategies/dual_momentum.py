from strategies.base import Base
from bot.models.kline import KLine
from bot.models.trade import (
    ExitReason,
    Trade, 
    TradeDirection, 
    is_trailing_stop,
    is_greedy_profit_reached,
    is_atr_stop_loss,
    get_current_profit_percentage,
)
from bot.exchange.binance import BinanceInterval, get_kline
from typing import Optional


_LOOCKBACK = 501 # precisely 501 is required to properly calculate 200 ema
_OVERBOUGHT = 80
_OVERSOLD = 20
_MIN_SLOPE = 5

class DualMomentum(Base):
    def __init__(
            self, 
            timeframe: BinanceInterval=BinanceInterval.day, 
            name='dual_momentum',
            hold_period_hours:Optional[float] = None,
            hold_exit_reason:Optional[set] = set(),
            trailing_stop_percentage:Optional[float] = None,
            trailing_start_percentage:Optional[float] = None,
            greedy_profit_percentage:Optional[float] = None,
            is_lower_timeframe_confirmation:bool = False,
            is_over_price_exit:bool = False,
            hard_stop_loss_percentage:Optional[float] = None,
            stop_loss_atr_percentage:Optional[float] = None,
        ):
        super().__init__(timeframe, _LOOCKBACK, name, hold_period_hours, hold_exit_reason)
        self.trailing_start_percentage = trailing_start_percentage
        self.trailing_stop_percentage = trailing_stop_percentage
        self.greedy_profit_percentage = greedy_profit_percentage
        self.is_lower_timeframe_confirmation = is_lower_timeframe_confirmation
        self.is_over_price_exit = is_over_price_exit
        self.hard_stop_loss_percentage = hard_stop_loss_percentage
        self.stop_loss_atr_percentage = stop_loss_atr_percentage

    def determine_trade_direction(self, kline: KLine, symbol: str) -> Optional[TradeDirection]:
        kline.add_ema(KLine.Col.ema_200, 200)
        kline.add_gmma()
        kline.add_stoch(5, 3, 2, KLine.Col.stoch_short_d, KLine.Col.stoch_short_k)
        kline.add_stoch(20, 3, 8, KLine.Col.stoch_long_d, KLine.Col.stoch_long_k)
        kline.add_rsi()

        direction = None

        if self.is_long_entry(kline):
            direction = TradeDirection.long
        elif self.is_short_entry(kline):
            direction = TradeDirection.short

        if (direction 
            and self.is_lower_timeframe_confirmation 
            and not self.is_lower_timeframe_confirmed(direction, symbol)):
            direction = None

        return direction
    

    def determine_exit_reason(self, kline: KLine, trade: Trade) -> Optional[ExitReason]:
        kline.add_stoch(5, 3, 2, KLine.Col.stoch_short_d, KLine.Col.stoch_short_k)
        kline.add_stoch(20, 3, 8, KLine.Col.stoch_long_d, KLine.Col.stoch_long_k)
        kline.add_rsi()

        reason = None
        if trade.direction == TradeDirection.long.value and self.is_long_exit(kline):
            reason = ExitReason.long_exit
        elif trade.direction == TradeDirection.short.value and self.is_short_exit(kline):
            reason = ExitReason.short_exit
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
            self.trailing_stop_percentage,
            self.trailing_start_percentage
        ):
            reason = ExitReason.trailing_stop
        elif self.is_over_price_exit and self.is_over_price(kline, trade.direction):
            reason = ExitReason.overprice_exit
        elif (self.hard_stop_loss_percentage 
              and get_current_profit_percentage(kline.get_running_price(), trade) < self.hard_stop_loss_percentage):
            reason = ExitReason.overprice_exit
        elif self.stop_loss_atr_percentage:
            current_profit_percentage = get_current_profit_percentage(kline.get_running_price(), trade)
            current_atr_percentage = kline.get_current_atr_percentage()
            if (current_profit_percentage < 0 
                and abs(current_profit_percentage / current_atr_percentage) >= self.stop_loss_atr_percentage):
                reason = ExitReason.stop_loss_atr_percentage

        return reason
    

    def is_lower_timeframe_confirmed(self, direction: TradeDirection, symbol: str) -> bool:
        lower_kline = get_kline(symbol, BinanceInterval.h4, _LOOCKBACK)
        lower_kline.add_rsi()
        lower_kline.add_mfi()

        return (
            (direction.value == TradeDirection.long.value and self.is_lower_timeframe_long_entry(lower_kline))
            or
            (direction.value == TradeDirection.short.value and self.is_lower_timeframe_short_entry(lower_kline))
        )
            

    def is_lower_timeframe_long_entry(self, kline: KLine):    
        return (
            kline.is_upward(KLine.Col.rsi)
            and kline.is_min_slope_diff(KLine.Col.rsi, _MIN_SLOPE)
            and kline.is_between(KLine.Col.rsi, 50, _OVERBOUGHT)

            and kline.is_upward(KLine.Col.mfi)
            and kline.is_min_slope_diff(KLine.Col.mfi, _MIN_SLOPE)
            and kline.is_between(KLine.Col.mfi, _OVERSOLD, _OVERBOUGHT)
        )
    

    def is_lower_timeframe_short_entry(self, kline: KLine):
        return (
            kline.is_downward(KLine.Col.rsi)
            and kline.is_min_slope_diff(KLine.Col.rsi, _MIN_SLOPE)
            and kline.is_between(KLine.Col.rsi, _OVERSOLD, 50)

            and kline.is_downward(KLine.Col.mfi)
            and kline.is_min_slope_diff(KLine.Col.mfi, _MIN_SLOPE)
            and kline.is_between(KLine.Col.mfi, _OVERSOLD, _OVERBOUGHT)
        ) 
    

    def is_over_price(self, kline: KLine, direction: TradeDirection):
        # an asset was overbought/oversold, and now it is exiting that zone,
        # meaning it is time to exit, because of trend reversal
        prev_stoch_short = kline.df[KLine.Col.stoch_short_d].iloc[-2]
        prev_stoch_long = kline.df[KLine.Col.stoch_long_d].iloc[-2]
        prev_rsi = kline.df[KLine.Col.rsi].iloc[-2]
        is_over_price = False

        if direction == TradeDirection.long.value:
            is_over_price = (
                (
                    prev_stoch_short > _OVERBOUGHT 
                    and kline.is_below(KLine.Col.stoch_short_d, _OVERBOUGHT)
                    and kline.is_downward(KLine.Col.stoch_short_d)
                )
                or (
                    prev_stoch_long > _OVERBOUGHT 
                    and kline.is_below(KLine.Col.stoch_long_d, _OVERBOUGHT)
                    and kline.is_downward(KLine.Col.stoch_long_d)
                )
                or (
                    prev_rsi > _OVERBOUGHT 
                    and kline.is_below(KLine.Col.rsi, _OVERBOUGHT)
                    and kline.is_downward(KLine.Col.rsi)
                )
            )
        else:
            is_over_price = (
                (
                    prev_stoch_short < _OVERSOLD 
                    and kline.is_above(KLine.Col.stoch_short_d, _OVERSOLD)
                    and kline.is_upward(KLine.Col.stoch_short_d)
                )
                or (
                    prev_stoch_long < _OVERSOLD 
                    and kline.is_above(KLine.Col.stoch_long_d, _OVERSOLD)
                    and kline.is_upward(KLine.Col.stoch_long_d)
                )
                or (
                    prev_rsi < _OVERSOLD 
                    and kline.is_above(KLine.Col.rsi, _OVERSOLD)
                    and kline.is_upward(KLine.Col.rsi)
                )
            )
        return is_over_price


    def is_long_entry(self, kline: KLine):      
        return (
            kline.is_upward(KLine.Col.ema_200)

            and kline.is_long_gmma_above_200ema()
            and kline.is_long_gmma_upward()

            and kline.is_short_term_GMMA_above_long_term_GMMA()
            and kline.is_short_gmma_upward()

            and kline.is_upward(KLine.Col.stoch_short_d)
            and kline.is_upward(KLine.Col.stoch_long_d)

            and kline.is_upward(KLine.Col.rsi)
            and kline.is_above(KLine.Col.rsi, 50)

            and kline.is_between(KLine.Col.stoch_long_d, _OVERSOLD, _OVERBOUGHT)
            and kline.is_between(KLine.Col.stoch_short_d, _OVERSOLD, 70)

            and kline.is_price_action_not_mixing_with_gmma(TradeDirection.long)
        )
    

    def is_short_entry(self, kline: KLine):
        return (
            kline.is_downward(KLine.Col.ema_200)

            and kline.is_long_gmma_below_200ema()
            and kline.is_long_gmma_downward()

            and kline.is_short_term_GMMA_below_long_term_GMMA()
            and kline.is_short_gmma_downward()

            and kline.is_downward(KLine.Col.stoch_short_d)
            and kline.is_downward(KLine.Col.stoch_long_d)

            and kline.is_downward(KLine.Col.rsi)
            and kline.is_below(KLine.Col.rsi, 50)

            and kline.is_between(KLine.Col.stoch_long_d, _OVERSOLD, _OVERBOUGHT)
            and kline.is_between(KLine.Col.stoch_short_d, 30, _OVERBOUGHT)

            and kline.is_price_action_not_mixing_with_gmma(TradeDirection.short)
        )
    

    def is_long_exit(self, kline: KLine):
        return (
            (
                kline.is_downward(KLine.Col.stoch_long_d)
                and kline.is_downward(KLine.Col.stoch_short_d)
            ) or (
                kline.is_below(KLine.Col.rsi, 50)
                and kline.is_downward(KLine.Col.rsi)
            )
        )


    def is_short_exit(self, kline: KLine):
        return (
            (
                kline.is_upward(KLine.Col.stoch_long_d)
                and kline.is_upward(KLine.Col.stoch_short_d)
            ) or (
                kline.is_upward(KLine.Col.rsi)
                and kline.is_above(KLine.Col.rsi, 50)
            )
        )