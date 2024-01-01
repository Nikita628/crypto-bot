from abc import ABC, abstractmethod
import time
from typing import Optional
from bot.kline import KLine
from bot.binance import get_kline, get_all_usdt_symbols, RateLimitException
from bot.trade import (
    TradeDirection,
    Trade,
    enter,
    exit,
    extend,
    get_all_active,
    is_already_trading,
)
from bot.binance import BinanceInterval
from integration.telegram import post_signal, TradeSignal

class Base(ABC):
    def __init__(self, timeframe: BinanceInterval, loockback: int, strategy: str) -> None:
        self.timeframe = timeframe
        self.loockback = loockback
        self.strategy = strategy

    def search_entry(self):
        try:
            usdt_symbols = sorted(get_all_usdt_symbols())

            while True:      
                for symbol in usdt_symbols:
                    try:
                        if is_already_trading(symbol, self.strategy):
                            continue

                        kline = get_kline(symbol, self.timeframe, self.loockback)

                        if len(kline.df) < self.loockback:
                            continue
                    
                        direction = self.determine_trade_direction(kline)  
                        kline.add_atr()    
                        current_atr_value = kline.df[KLine.Col.atr].iloc[-1]
                        current_price = kline.get_running_price()

                        if direction:
                            deal = Trade(
                                base_asset=symbol.replace('USDT', ''),
                                quote_asset='USDT',
                                entry_price=kline.get_running_price(),
                                direction=direction,
                                strategy=self.strategy,
                                atr_percentage=current_atr_value / current_price * 100
                            )
                            enter(deal)
                            self.log(f'entered {symbol}')

                            # TODO: only volume surge for chart analysis for now, later all strategies
                            if self.strategy.startswith('volume_surge'):
                                post_signal(TradeSignal(
                                    strategy=self.strategy,
                                    symbol=symbol,
                                    is_entry=True,
                                    is_long=direction.value == TradeDirection.long.value,
                                ))
                    except RateLimitException as e:
                        raise e
                    except Exception as e:
                        self.log(f"search_entry: Failed to process data for {symbol}: {e}")
                            
                    time.sleep(5)
                        
                time.sleep(300)
        except RateLimitException as e:
            self.log(f"search_entry: rate limit error {e}")
            raise e
        except Exception as e:
            self.log(f'search_entry: global error {e}')
            raise e

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
                            exit(trade.id, running_price, exit_reason)
                            self.log(f'exited {trade.symbol}, reason {exit_reason}')

                            # TODO: only volume surge for chart analysis for now, later all strategies
                            if self.strategy.startswith('volume_surge'):
                                post_signal(TradeSignal(
                                        strategy=self.strategy, 
                                        symbol=trade.symbol, 
                                        exit_reason=exit_reason
                                    ))
                        else:
                            extend(trade.id, running_price)
                    except RateLimitException as e:
                        raise e
                    except Exception as e:
                        self.log(f"search_exit: Failed to process data for {trade.base_asset}: {e}")

                time.sleep(60)
        except RateLimitException as e:
            self.log(f"search_exit: rate limit error {e}")
            raise e
        except Exception as e:
            self.log(f'search_exit: global error {e}')
            raise e


    @abstractmethod
    def determine_exit_reason(self, kline: KLine, deal: Trade) -> Optional[str]:
        pass

    @abstractmethod
    def determine_trade_direction(self, kline: KLine) -> Optional[TradeDirection]:
        pass

    def log(self, msg: str):
        print(f'{self.strategy}: {msg}')
