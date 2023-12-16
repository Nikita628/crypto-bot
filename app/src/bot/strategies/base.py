from abc import ABC, abstractmethod
import datetime
import time
import pandas as pd

class Base(ABC):
    def search_entry(self):
        try:
            usdt_symbols = sorted(get_all_usdt_symbols())

            while True:                
                for symbol in usdt_symbols:
                    try:
                        if is_symbol_in_open_deal(symbol, 1):
                            continue

                        df = get_kline(symbol, self.interval, self.loockback)

                        if len(df) < self.loockback:
                            continue
                
                        deal_direction = self.get_entry_direction(df)

                        if deal_direction:
                            deal = Deal(
                                base_asset=symbol.replace('USDT', ''),
                                quote_asset='USDT',
                                entry_price=df['close'].iloc[-1],
                                entry_date=datetime.datetime.utcnow(),
                                direction=deal_direction,
                                exit_price=None,
                                exit_date=None,
                                profit_percentage=0,
                                running_profit_percentage=0,
                                running_price=0, # TODO: = should be equal entry price
                                user_id=1
                            )
                            create_deal(deal)
                            # TODO: deal.enter(deal)
                    
                    except Exception as e:
                        print(f"Failed to process data for {symbol}: {e}")
                        
                    time.sleep(2)
                    
                time.sleep(300) # 5 minutes
        except:
            print(f"search_entry error")


    def search_exit(self):
        try:
            while True:
                open_deals = get_open_deals()

                for deal in open_deals:
                    try:
                        df = get_kline(deal.symbol, self.intervarl, self.loockback)
                        
                        if self.is_exit(df, deal):
                            deal.exit(id, running_price)
                        # TODO: all below should be gone

                        if deal.direction == DealDirection.long.value and self.is_long_exit(df, deal):
                            # sell long
                            ######################
                            ### TODO: this all must be pushed down the level of deal db model
                            exit_price = df['close'].iloc[-1]
                            exit_date =  datetime.datetime.utcnow()
                            profit = df['close'].iloc[-1] - float(deal.entry_price)
                            profit_percentage = profit * 100 / float(deal.entry_price)
                            exit_deal(exit_price, exit_date, profit_percentage, deal.symbol, 1)
                            #######################
                            # TODO: deal.exit(id, running_price)
                        elif deal.direction == DealDirection.short.value and self.is_short_exit(df, deal):
                            # sell short
                            exit_price = df['close'].iloc[-1]
                            exit_date =  datetime.datetime.utcnow()
                            profit = float(deal.entry_price) - df['close'].iloc[-1]
                            profit_percentage = profit * 100 / float(deal.entry_price)
                            exit_deal(exit_price, exit_date, profit_percentage, deal.symbol, 1)
                            # TODO: deal.exit(id, running_price)
                        else:
                            profit = (
                                df['close'].iloc[-1] - float(deal.entry_price) 
                                if deal.direction == DealDirection.long.value
                                else float(deal.entry_price) - df['close'].iloc[-1]
                            )
                            running_profit_percentage = profit * 100 / float(deal.entry_price)
                            running_price =  df['close'].iloc[-1]
                            update_deal(running_profit_percentage, running_price, deal.symbol, 1)
                            # TODO: deal.extend(id, running_price)
                    except Exception as e:
                        print(f"Failed to process data for {deal.symbol}: {e}")
                time.sleep(300)  # 5 minutes
        except:
            print(f"search_exit error")


    @abstractmethod
    def is_exit(self, df: pd.DataFrame, deal: Deal) -> bool:
        pass

    @abstractmethod
    def get_entry_direction(self, df: pd.DataFrame) -> DealDirection or None:
        pass
