from bot.kline import KLine
from bot.trade import (
    Trade, 
    TradeDirection, 
    is_trailing_stop,
    is_greedy_profit_reached,
    is_atr_stop_loss,
    get_current_profit_percentage,
)
from bot.binance import BinanceInterval, get_kline
from typing import Optional
from strategies.base import Base

_LOOCKBACK = 501 # precisely 501 is required to properly calculate 200 ema

# customized dual momentum

# additional check if rsi is overbought/oversold

# additional check of volume sma

# additional check of mfi upward, overbought/oversold

# additional check on stochastics - they should both be going
# in one direction, and not overbought/oversold

_MIN_SLOPE = 2
_OVERBOUGHT = 80
_OVERSOLD = 20

class DualMomentumCustomized(Base):
    def __init__(
            self, 
            timeframe:BinanceInterval = BinanceInterval.day, 
            name = 'dual_momentum_customized',
            trailing_stop_percentage:Optional[float] = None,
            greedy_profit_percentage:Optional[float] = None,
            hard_stop_loss_percentage:Optional[float] = None,
            is_over_price_exit:bool = False,
            is_lower_timeframe_confirmation:bool = False,
            atr_limit:Optional[float] = None,
            # reference values:
            # x > 10 - high, x < 5 - low
            volatility_limit:Optional[float] = None,
        ):
        super().__init__(timeframe, _LOOCKBACK, name)
        self.trailing_stop_percentage = trailing_stop_percentage
        self.greedy_profit_percentage = greedy_profit_percentage
        self.hard_stop_loss_percentage = hard_stop_loss_percentage
        self.is_over_price_exit = is_over_price_exit
        self.is_lower_timeframe_confirmation = is_lower_timeframe_confirmation
        self.atr_limit = atr_limit
        self.volatility_limit = volatility_limit

    def determine_trade_direction(self, kline: KLine, symbol: str) -> Optional[TradeDirection]:
        kline.add_ema(KLine.Col.ema_200, 200)
        kline.add_gmma()
        kline.add_stoch(5, 3, 2, KLine.Col.stoch_short_d, KLine.Col.stoch_short_k)
        kline.add_stoch(20, 3, 8, KLine.Col.stoch_long_d, KLine.Col.stoch_long_k)
        kline.add_rsi()
        kline.add_sma(KLine.Col.volume_sma, KLine.Col.volume)
        kline.add_mfi()

        direction = None

        if self.atr_limit and self.atr_limit > 0:
            atr = kline.df[KLine.Col.atr].iloc[-1]
            price = kline.df[KLine.Col.close].iloc[-1]
            atr_percentage = atr / price * 100
            if atr_percentage > self.atr_limit:
                return None
            
        if self.volatility_limit and self.volatility_limit > 0:
            if kline.calc_volatility(30) > self.volatility_limit:
                return None
            
        if self.is_long_entry(kline):
            direction = TradeDirection.long
        elif self.is_short_entry(kline):
            direction = TradeDirection.short

        if (direction 
            and self.is_lower_timeframe_confirmation 
            and not self.is_lower_timeframe_confirmed(direction, symbol)):
            direction = None

        return direction
        

    def determine_exit_reason(self, kline: KLine, trade: Trade) -> Optional[str]:
        kline.add_stoch(5, 3, 2, KLine.Col.stoch_short_d, KLine.Col.stoch_short_k)
        kline.add_stoch(20, 3, 8, KLine.Col.stoch_long_d, KLine.Col.stoch_long_k)
        kline.add_rsi()
        kline.add_mfi()

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
            reason = 'gready percentage'
        elif self.trailing_stop_percentage and is_trailing_stop(
            kline.get_running_price(), 
            trade, 
            self.trailing_stop_percentage
        ):
            reason = 'trailing stop'
        elif (self.hard_stop_loss_percentage and get_current_profit_percentage(kline.get_running_price(), trade) < self.hard_stop_loss_percentage):
            reason = 'hard stop loss'
        elif self.is_over_price_exit and self.is_over_price(kline, trade.direction):
            reason = 'overprice exit'
            
        return reason
    
    def is_lower_timeframe_confirmed(self, direction: TradeDirection, symbol: str) -> bool:
        lower_kline = get_kline(symbol, BinanceInterval.h4, _LOOCKBACK)
        # lower_kline.add_ema(KLine.Col.ema_200, 200)
        # lower_kline.add_gmma()
        # lower_kline.add_stoch(5, 3, 2, KLine.Col.stoch_short_d, KLine.Col.stoch_short_k)
        # lower_kline.add_stoch(20, 3, 8, KLine.Col.stoch_long_d, KLine.Col.stoch_long_k)
        lower_kline.add_rsi()
        lower_kline.add_mfi()

        return (
            (direction.value == TradeDirection.long.value and self.is_lower_timeframe_long_entry(lower_kline))
            or
            (direction.value == TradeDirection.short.value and self.is_lower_timeframe_short_entry(lower_kline))
        )


    def is_lower_timeframe_long_entry(self, kline: KLine):    
        return all([
            # kline.is_upward(KLine.Col.ema_200), 

            # kline.is_long_gmma_above_200ema(), 
            # kline.is_long_gmma_upward(),

            # kline.is_short_term_GMMA_above_long_term_GMMA(),
            # kline.is_short_gmma_upward(),

            # kline.is_upward(KLine.Col.stoch_short_d),
            # kline.is_upward(KLine.Col.stoch_long_d),
            # kline.is_between(KLine.Col.stoch_long_d, 20, overbought_limit),
            # kline.is_between(KLine.Col.stoch_short_d, 20, overbought_limit),

            # kline.is_price_action_not_mixing_with_gmma(TradeDirection.long),

            kline.is_upward(KLine.Col.rsi),
            kline.is_min_slope_diff(KLine.Col.rsi, _MIN_SLOPE),
            kline.is_between(KLine.Col.rsi, 50, _OVERBOUGHT),

            kline.is_upward(KLine.Col.mfi),
            kline.is_min_slope_diff(KLine.Col.mfi, _MIN_SLOPE),
            kline.is_between(KLine.Col.mfi, _OVERSOLD, _OVERBOUGHT),
        ])
    

    def is_lower_timeframe_short_entry(self, kline: KLine):
        return all([
            # kline.is_downward(KLine.Col.ema_200), 

            # kline.is_long_gmma_below_200ema(), 
            # kline.is_long_gmma_downward(),

            # kline.is_short_term_GMMA_below_long_term_GMMA(),
            # kline.is_short_gmma_downward(),

            # kline.is_downward(KLine.Col.stoch_short_d),
            # kline.is_downward(KLine.Col.stoch_long_d),
            # kline.is_between(KLine.Col.stoch_long_d, oversold_limit, 80),
            # kline.is_between(KLine.Col.stoch_short_d, oversold_limit, 80),

            # kline.is_price_action_not_mixing_with_gmma(TradeDirection.short),

            kline.is_downward(KLine.Col.rsi),
            kline.is_min_slope_diff(KLine.Col.rsi, _MIN_SLOPE),
            kline.is_between(KLine.Col.rsi, _OVERSOLD, 50),

            kline.is_downward(KLine.Col.mfi),
            kline.is_min_slope_diff(KLine.Col.mfi, _MIN_SLOPE),
            kline.is_between(KLine.Col.mfi, _OVERSOLD, _OVERBOUGHT),
        ]) 


    def is_over_price(self, kline: KLine, direction: TradeDirection):
        prev_stoch_short = kline.df[KLine.Col.stoch_short_d].iloc[-2]
        prev_stoch_long = kline.df[KLine.Col.stoch_long_d].iloc[-2]
        prev_rsi = kline.df[KLine.Col.rsi].iloc[-2]
        prev_mfi = kline.df[KLine.Col.mfi].iloc[-2]

        if direction == TradeDirection.long.value:
            return (
                any([
                    (prev_stoch_short > _OVERBOUGHT 
                     and kline.is_below(KLine.Col.stoch_short_d, _OVERBOUGHT)
                     and kline.is_downward(KLine.Col.stoch_short_d)),
                    (prev_stoch_long > _OVERBOUGHT 
                     and kline.is_below(KLine.Col.stoch_long_d, _OVERBOUGHT)
                     and kline.is_downward(KLine.Col.stoch_long_d)),
                    (prev_rsi > _OVERBOUGHT 
                     and kline.is_below(KLine.Col.rsi, _OVERBOUGHT)
                     and kline.is_downward(KLine.Col.rsi)),
                    (prev_mfi > _OVERBOUGHT 
                     and kline.is_below(KLine.Col.mfi, _OVERBOUGHT)
                     and kline.is_downward(KLine.Col.mfi)),
                ])
            )
        else:
            return (
                any([
                    (prev_stoch_short < _OVERSOLD 
                     and kline.is_above(KLine.Col.stoch_short_d, _OVERSOLD)
                     and kline.is_upward(KLine.Col.stoch_short_d)),
                    (prev_stoch_long < _OVERSOLD 
                     and kline.is_above(KLine.Col.stoch_long_d, _OVERSOLD)
                     and kline.is_upward(KLine.Col.stoch_long_d)),
                    (prev_rsi < _OVERSOLD 
                     and kline.is_above(KLine.Col.rsi, _OVERSOLD)
                     and kline.is_upward(KLine.Col.rsi)),
                    (prev_mfi < _OVERSOLD 
                     and kline.is_above(KLine.Col.mfi, _OVERSOLD)
                     and kline.is_upward(KLine.Col.mfi)),
                ])
            )


    def is_long_entry(self, kline: KLine):    
        return all([
            kline.is_upward(KLine.Col.ema_200), 

            kline.is_long_gmma_above_200ema(), 
            kline.is_long_gmma_upward(),

            kline.is_short_term_GMMA_above_long_term_GMMA(),
            kline.is_short_gmma_upward(),

            kline.is_upward(KLine.Col.stoch_short_d),
            kline.is_between(KLine.Col.stoch_short_d, _OVERSOLD, 70),

            kline.is_upward(KLine.Col.stoch_long_d),
            kline.is_between(KLine.Col.stoch_long_d, _OVERSOLD, _OVERBOUGHT),

            kline.is_upward(KLine.Col.rsi),
            kline.is_between(KLine.Col.rsi, 50, _OVERBOUGHT),
            kline.is_min_slope_diff(KLine.Col.rsi, _MIN_SLOPE),

            kline.is_price_action_not_mixing_with_gmma(TradeDirection.long),

            # custom tech indicators additionally to dual momentum 
            kline.is_upward(KLine.Col.mfi),
            kline.is_between(KLine.Col.mfi, _OVERSOLD, _OVERBOUGHT),
            kline.is_min_slope_diff(KLine.Col.mfi, _MIN_SLOPE),
        ])
    

    def is_short_entry(self, kline: KLine):
        return all([
            kline.is_downward(KLine.Col.ema_200), 

            kline.is_long_gmma_below_200ema(), 
            kline.is_long_gmma_downward(),

            kline.is_short_term_GMMA_below_long_term_GMMA(),
            kline.is_short_gmma_downward(),

            kline.is_downward(KLine.Col.stoch_short_d),
            kline.is_between(KLine.Col.stoch_short_d, 30, _OVERBOUGHT),

            kline.is_downward(KLine.Col.stoch_long_d),
            kline.is_between(KLine.Col.stoch_long_d, _OVERSOLD, _OVERBOUGHT),

            kline.is_downward(KLine.Col.rsi),
            kline.is_between(KLine.Col.rsi, _OVERSOLD, 50),
            kline.is_min_slope_diff(KLine.Col.rsi, _MIN_SLOPE),

            kline.is_price_action_not_mixing_with_gmma(TradeDirection.short),

            # custom tech indicators additionally to dual momentum      
            kline.is_downward(KLine.Col.mfi),
            kline.is_between(KLine.Col.mfi, _OVERSOLD, _OVERBOUGHT),
            kline.is_min_slope_diff(KLine.Col.mfi, _MIN_SLOPE),
        ])
    
    def is_long_exit(self, kline: KLine):
        return (
            all([
                kline.is_downward(KLine.Col.stoch_long_d),
                kline.is_downward(KLine.Col.stoch_short_d),
            ]) or all([
                kline.is_below(KLine.Col.rsi, 50),
                kline.is_downward(KLine.Col.rsi),
            ])
        )

    def is_short_exit(self, kline: KLine):
        return (
            all([
                kline.is_upward(KLine.Col.stoch_long_d),
                kline.is_upward(KLine.Col.stoch_short_d),
            ]) or all ([
                kline.is_upward(KLine.Col.rsi),
                kline.is_above(KLine.Col.rsi, 50),
            ])
        )