from abc import ABC, abstractmethod
import datetime
import time
from ..binance import get_kline, get_all_usdt_symbols
from ..technical_indicators import DataFrameDecorator
from ..core import KLineShape
from ..deal import (
    DealDirection,
    Deal,
    enter,
    exit,
    extend,
    get_all_opened,
    is_asset,
)

class Base(ABC):
    def search_entry(self):
        usdt_symbols = sorted(get_all_usdt_symbols())

        while True:                
            for symbol in usdt_symbols:
                try:
                    if is_asset(symbol):
                        continue

                    df = get_kline(symbol, self.interval, self.loockback)

                    if len(df.df) < self.loockback:
                        continue
                
                    deal_direction = self.get_entry_direction(df)

                    if deal_direction:
                        deal = Deal(
                            base_asset=symbol.replace('USDT', ''),
                            quote_asset='USDT',
                            entry_price=df.df['close'].iloc[-1],
                            entry_date=datetime.datetime.utcnow(),
                            direction=deal_direction,
                            exit_price=None,
                            exit_date=None,
                            running_price=df.df['close'].iloc[-1],
                            strategy=self.strategy,
                        )
                        enter(deal)
                except Exception as e:
                    print(f"Failed to process data for {symbol}: {e}")
                        
                time.sleep(2)
                    
            time.sleep(300)


    def search_exit(self):
        while True:
            open_deals = get_all_opened()

            for deal in open_deals:
                try:
                    df = get_kline(deal.symbol, self.interval, self.loockback)
                    running_price = df.df[KLineShape.close].iloc[-1]

                    if self.is_exit(df, deal):
                        exit(deal.id, running_price)
                    else:
                        extend(deal.id, running_price)

                except Exception as e:
                    print(f"Failed to process data for {deal.base_asset}: {e}")

            time.sleep(300)


    @abstractmethod
    def is_exit(self, df: DataFrameDecorator, deal: Deal) -> bool:
        pass

    @abstractmethod
    def get_entry_direction(self, df: DataFrameDecorator) -> DealDirection or None:
        pass
