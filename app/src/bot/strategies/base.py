from abc import ABC, abstractmethod
import time
from bot.kline import KLine
from bot.binance import get_kline, get_all_usdt_symbols
from bot.deal import (
    TradeDirection,
    Deal,
    enter,
    exit,
    extend,
    get_all_opened,
    is_asset,
)
from bot.binance import BinanceInterval

class Base(ABC):
    def __init__(self, timeframe: BinanceInterval, loockback: int, strategy: str) -> None:
        self.timeframe = timeframe
        self.loockback = loockback
        self.strategy = strategy

    def search_entry(self):
        usdt_symbols = sorted(get_all_usdt_symbols())
        self.log(f'will check {len(usdt_symbols)} usdt symbols for entry')

        while True:      
            self.log('searching entry...')
            checked_symbols = 0

            for symbol in usdt_symbols:
                checked_symbols += 1
                if (checked_symbols % 10 == 0):
                    self.log(f'total symbols checked: {checked_symbols}')

                try:
                    if is_asset(symbol):
                        continue

                    kline = get_kline(symbol, self.timeframe, self.loockback)

                    if len(kline.df) < self.loockback:
                        continue
                
                    direction = self.determine_trade_direction(kline)                 

                    if direction:
                        deal = Deal(
                            base_asset=symbol.replace('USDT', ''),
                            quote_asset='USDT',
                            entry_price=kline.get_running_price(),
                            direction=direction,
                            strategy=self.strategy,
                        )
                        enter(deal)
                        self.log(f'entered {symbol}')
                except Exception as e:
                    self.log(f"search_entry: Failed to process data for {symbol}: {e}")
                        
                time.sleep(5)
                    
            time.sleep(300)


    def search_exit(self):
        while True:
            self.log('searching exit...')
            open_deals = get_all_opened(self.strategy)

            self.log(f'will check {len(open_deals)} deals for exit')

            for deal in open_deals:
                try:
                    kline = get_kline(deal.symbol, self.timeframe, self.loockback)
                    running_price = kline.get_running_price()

                    if self.is_exit(kline, deal):
                        exit(deal.id, running_price)
                        self.log(f'exited {deal.symbol}')
                    else:
                        extend(deal.id, running_price)

                except Exception as e:
                    self.log(f"search_exit: Failed to process data for {deal.base_asset}: {e}")

            time.sleep(60)


    @abstractmethod
    def is_exit(self, kline: KLine, deal: Deal) -> bool:
        pass

    @abstractmethod
    def determine_trade_direction(self, kline: KLine) -> TradeDirection or None:
        pass

    def log(self, msg: str):
        print(f'{self.strategy}: {msg}')
