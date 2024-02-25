from abc import ABC, abstractmethod
import time
import datetime
from typing import Optional
from bot.models.kline import KLine
from bot.exchange.binance import get_kline, get_all_usdt_symbols, RateLimitException
from bot.models.trade import (
    ExitReason,
    TradeDirection,
    Trade,
    enter,
    exit,
    extend,
    get_all_active,
    is_already_trading,
    get_current_profit_percentage,
)
import bot.models.asset as asset
import bot.models.hold as hold
from bot.exchange.binance import BinanceInterval
from typing import Optional
from integration.telegram import post_signal, post_error, TradeEntrySignal, TradeExitSignal

_MIN_ATR_PERCENTAGE = 1

class IndicatorSettings:
    def __init__(
            self,
            ema_200_upward_lookback = 1,
            ema_200_downward_lookback = 1,
            long_gmma_above_200_ema_lookback = 1,
            long_gmma_below_200_ema_lookback = 1,
            short_gmma_above_long_gmma_lookback = 1,
            short_gmma_below_long_gmma_lookback = 1,
            long_gmma_upward_lookback = 1,
            long_gmma_downward_lookback = 1,
            short_gmma_upward_lookback = 1,
            short_gmma_downward_lookback = 1,
        ):
        self.ema_200_upward_lookback = ema_200_upward_lookback
        self.ema_200_downward_lookback = ema_200_downward_lookback
        self.long_gmma_above_200_ema_lookback = long_gmma_above_200_ema_lookback
        self.long_gmma_below_200_ema_lookback = long_gmma_below_200_ema_lookback
        self.short_gmma_above_long_gmma_lookback = short_gmma_above_long_gmma_lookback
        self.short_gmma_below_long_gmma_lookback = short_gmma_below_long_gmma_lookback
        self.long_gmma_upward_lookback = long_gmma_upward_lookback
        self.long_gmma_downward_lookback = long_gmma_downward_lookback
        self.short_gmma_upward_lookback = short_gmma_upward_lookback
        self.short_gmma_downward_lookback = short_gmma_downward_lookback
        

class Base(ABC):
    def __init__(
            self,
            timeframe: BinanceInterval,
            loockback: int,
            strategy: str,
            hold_period_hours:Optional[float] = None,
            hold_exit_reason:Optional[set] = set(),
        ) -> None:
        self.timeframe = timeframe
        self.loockback = loockback
        self.strategy = strategy
        self.hold_period_hours = hold_period_hours
        self.hold_exit_reason = hold_exit_reason

    def search_entry(self):
        try:
            usdt_symbols = sorted(get_all_usdt_symbols())

            while True:      
                for symbol in usdt_symbols:
                    try:
                        if is_already_trading(symbol, self.strategy):
                            continue

                        if hold.is_active(symbol, self.strategy):
                            continue

                        kline = get_kline(symbol, self.timeframe, self.loockback)

                        if len(kline.df) < self.loockback:
                            continue

                        kline.add_atr()
                        atr_percentage = kline.get_current_atr_percentage()

                        if atr_percentage < _MIN_ATR_PERCENTAGE:
                            continue

                        current_price = kline.get_running_price()
                        direction = self.determine_trade_direction(kline, symbol)

                        if direction:
                            trade = Trade(
                                base_asset=symbol.replace('USDT', ''),
                                base_asset_amount=asset.AssetConstants.per_trade_ustd_amount/current_price,
                                quote_asset='USDT',
                                entry_price=current_price,
                                direction=direction,
                                strategy=self.strategy,
                                atr_percentage=atr_percentage,
                            )

                            enter(trade)
                            
                            self.log(f'entered {symbol}')

                            post_signal(TradeEntrySignal(
                                strategy=self.strategy,
                                symbol=symbol,
                                is_long=direction.value == TradeDirection.long.value,
                                running_price=current_price,
                            ))
                    except RateLimitException as e:
                        raise e
                    except Exception as e:
                        self.log(f"search_entry: Failed to process data for {symbol}: {e}")
                        post_error(f"search_entry: Failed to process data for {symbol}: {e}")                        
                    time.sleep(2.5)
                time.sleep(60)
        except RateLimitException as e:
            self.log(f"search_entry: rate limit error {e}")
            post_error(f"search_entry: rate limit error {e}")
            raise e
        except Exception as e:
            self.log(f'search_entry: global error {e}')
            post_error(f'search_entry: global error {e}')


    def search_exit(self):
        try:
            while True:
                open_trades = get_all_active(self.strategy)

                for trade in open_trades:
                    try:
                        kline = get_kline(trade.symbol, self.timeframe, self.loockback)
                        running_price = kline.get_running_price()
                        exit_reason = self.determine_exit_reason(kline, trade)

                        if exit_reason:
                            exit(
                                trade,
                                running_price, 
                                exit_reason, 
                                self.strategy, 
                                self.hold_period_hours, 
                                self.hold_exit_reason
                            )

                            self.log(f'exited {trade.symbol}, reason {exit_reason.value}')

                            post_signal(TradeExitSignal(
                                strategy=self.strategy, 
                                symbol=trade.symbol, 
                                exit_reason=exit_reason.value,
                                running_price=running_price,
                                entry_price=trade.entry_price,
                                is_long=trade.direction == TradeDirection.long.value,
                                profit_percentage=get_current_profit_percentage(running_price, trade),
                            ))
                        else:
                            extend(trade.id, running_price)
                    except RateLimitException as e:
                        raise e
                    except Exception as e:
                        self.log(f"search_exit: Failed to process data for {trade.base_asset}: {e}")
                        post_error(f"search_exit: Failed to process data for {trade.base_asset}: {e}")
                time.sleep(30)
        except RateLimitException as e:
            self.log(f"search_exit: rate limit error {e}")
            post_error(f"search_exit: rate limit error {e}")
            raise e
        except Exception as e:
            self.log(f'search_exit: global error {e}')
            post_error(f'search_exit: global error {e}')


    @abstractmethod
    def determine_exit_reason(self, kline: KLine, deal: Trade) -> Optional[ExitReason]:
        pass

    @abstractmethod
    def determine_trade_direction(self, kline: KLine, symbol: str) -> Optional[TradeDirection]:
        pass

    def log(self, msg: str):
        print(f'{self.strategy}: {msg}')
