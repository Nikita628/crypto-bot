import datetime
import database.models
from enum import Enum
from typing import List

EXPIRATION_PERIOD_HOURS = 48

# TODO: rename file to deal.py

class DealDirection(Enum):
    long = 'long'
    short = 'short'

class Deal:
    def __init__(
            self,
            id: int,
            symbol: str,
            base_asset: str,
            quote_asset: str, 
            entry_price: float,
            entry_date: datetime.datetime,
            exit_price: float or None,
            exit_date: datetime.datetime or None,
            profit_percentage: float,
            running_price: float,
            direction: DealDirection,
            user_id: int,
            strategy: str
        ):
        self.id = id
        self.symbol = symbol
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.exit_price = exit_price
        self.exit_date = exit_date
        self.profit_percentage = profit_percentage
        self.running_price = running_price
        self.direction = direction
        self.user_id = user_id
        self.strategy = strategy

def map_deal(deal: database.models.Deal):
    return Deal(
        id = deal.id,
        symbol = deal.symbol,
        base_asset = deal.base_asset,
        quote_asset = deal.quote_asset,
        entry_price = deal.entry_price,
        entry_date = deal.entry_date,
        exit_price = deal.exit_price,
        exit_date = deal.exit_date,
        profit_percentage = deal.profit_percentage,
        running_price = deal.running_price,
        direction = deal.direction,
        user_id = deal.user_id,
        strategy = deal.strategy,
    )

USER_ID = 1

def is_asset(symbol: str):
    deal = (database.models.Deal.select().where(
        (database.models.Deal.symbol == symbol)
        & (database.models.Deal.exit_price.is_null(True))
        & (database.models.Deal.user_id == USER_ID)))
    
    return bool(deal)

def get_all_opened() -> List[Deal]:
    deals: List[database.models.Deal] = database.models.Deal.select().where(
       (database.models.Deal.exit_price.is_null(True))
        & (database.models.Deal.user_id == USER_ID))
    
    return list(map(map_deal, deals))


def is_expired(deal: Deal) -> bool:
    return deal and datetime.datetime.now() - deal.entry_date > EXPIRATION_PERIOD_HOURS*60*60


def is_trailing_stop_hit() -> bool:
    return False


def enter(deal: Deal):
    database.models.Deal.create(
           base_asset = deal.base_asset,
           quote_asset = deal.quote_asset,
           entry_price = deal.entry_price,
           entry_date = deal.entry_date,
           running_price = deal.entry_price,
           direction = deal.direction.value, 
           user_id = USER_ID
        )
    

def exit(id: int, running_price: float):
    query = database.models.Deal.update(
        exit_price = running_price,
        exit_date =  datetime.datetime.utcnow()
        ).where(
            (database.models.Deal.id == id) 
            & (database.models.Deal.user_id == USER_ID))
    query.execute()
    

def extend(id: int, running_price: float):
    query = database.models.Deal.update(
        running_price =  running_price
        ).where(
            (database.models.Deal.id == id)
            & (database.models.Deal.user_id == USER_ID))
    query.execute()
