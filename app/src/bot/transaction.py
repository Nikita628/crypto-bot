import threading
import datetime
import database.models
from enum import Enum
from typing import List

# connect DB and phycopg2
# add 'asset' table

# symbol,entry_price,entry_date,exit_price,exit_date,amount,
# running_profit_percentage,running_price,direction,is_for_trading,is_for_balance
EXPIRATION_PERIOD_HOURS = 48
#################################################

# TODO: rename file to deal.py

class DealDirection(Enum):
    long = 'long'
    short = 'short'

# convert to Asset
class Deal:
    def __init__(
            self,
            base_asset: str,
            quote_asset: str, 
            entry_price: float,
            entry_date: datetime.datetime,
            exit_price: float or None,
            exit_date: datetime.datetime or None,
            profit_percentage: float, # TODO: - remove, make computable in db
            running_profit_percentage: float, # - remove, make computable in db
            running_price: float,
            direction: DealDirection,
            user_id: int,
            # amount: float
        ):
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.exit_price = exit_price
        self.exit_date = exit_date
        self.profit_percentage = profit_percentage
        self.running_profit_percentage = running_profit_percentage
        self.running_price = running_price
        self.direction = direction
        self.user_id = user_id


# TODO: do not pass user_id, hardcode in this file, later will read from the context

# is_asset(symbol)
def is_symbol_in_open_deal(symbol: str, user_id: int):
    deal = (database.models.Deal.select().where(
        (database.models.Deal.symbol == symbol)
        & (database.models.Deal.exit_price.is_null(True))
        & (database.models.Deal.user_id == user_id)))
    if deal:
        print('true')
        return True
    print('false')
    return False

# get_assets()
def get_open_deals(user_id: int) -> List[Deal]:
    deals = database.models.Deal.select().where(
       (database.models.Deal.exit_price.is_null(True))
        & (database.models.Deal.user_id == user_id))
    # TODO: map to model, dont return from DB directly, because we don't want to mixup abstraction layers
    return deals


# asset is expired when price moves within range -/+ 0.5 % 
# more then 2 days in a row
def is_expired(deal: Deal) -> bool:
    if deal and datetime.datetime.now() - deal.entry_date > EXPIRATION_PERIOD_HOURS*60*60:
        return True
    return False



# get_balance()


def is_trailing_stop_hit() -> bool:
    return False

# buy_asset TODO: remove comments
def create_deal(deal: Deal):
    database.models.Deal.create(
           base_asset = deal.base_asset,
           quote_asset = deal.quote_asset,
           entry_price = deal.entry_price,
           entry_date = deal.entry_date, # TODO: should be filled in by DB, by default
           exit_price = deal.exit_price,
           exit_date = deal.exit_date,
           profit_percentage=deal.profit_percentage,
           running_profit_percentage = deal.running_profit_percentage,
           running_price = deal.entry_price,
           direction = deal.direction.value, 
           user_id = deal.user_id)
    
# sell_asset
# TODO: pass id of deal ?
def exit_deal(exit_price: float, exit_date: datetime, profit_percentage: float, symbol: str, user_id: int):
    query = database.models.Deal.update(
        exit_price = exit_price,
        exit_date =  exit_date,
        profit_percentage = profit_percentage
        ).where(
            (database.models.Deal.symbol == symbol) 
            & (database.models.Deal.user_id == user_id)) # TODO: replace & with 'and' ?
    query.execute()
    
# update deal
def update_deal(running_profit_percentage: float, running_price: float, symbol: str, user_id: int):
    query = database.models.Deal.update(
        running_profit_percentage = running_profit_percentage,
        running_price =  running_price
        ).where(
            (database.models.Deal.symbol == symbol)
            & (database.models.Deal.user_id == user_id))
    query.execute()
