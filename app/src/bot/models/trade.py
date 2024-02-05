import datetime
import database.models
from enum import Enum
from typing import List

_EXPIRATION_PERIOD_HOURS = 48

class ExitReason(Enum):
    any = 'any'
    long_exit = 'long exit'
    short_exit = 'short exit'
    atr_stop_loss = 'ATR stop loss'
    greedy_percentage = 'greedy percentage'
    trailing_stop = 'trailing stop'
    hard_stop_loss = 'hard stop loss'
    overprice_exit = 'overprice exit'

class TradeDirection(Enum):
    long = 'long'
    short = 'short'

class Trade:
    def __init__(
            self,
            id: int = None,
            symbol: str = None,
            base_asset: str = None,
            base_asset_amount: float = None,
            quote_asset: str = None,
            quote_asset_amount: float = None, 
            entry_price: float = None,
            entry_date: datetime.datetime = None,
            exit_price: float or None = None,
            exit_date: datetime.datetime or None = None,
            exit_reason: str = None,
            profit_percentage: float = None,
            highest_profit_percentage: float = None,
            running_price: float = None,
            direction: TradeDirection = None,
            user_id: int = None,
            strategy: str = None,
            atr_percentage: float = None,
        ):
        self.id = id
        self.symbol = symbol
        self.base_asset = base_asset
        self.base_asset_amount = base_asset_amount
        self.quote_asset = quote_asset
        self.quote_asset_amount = quote_asset_amount
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.exit_price = exit_price
        self.exit_date = exit_date
        self.exit_reason = exit_reason
        self.profit_percentage = profit_percentage
        self.highest_profit_percentage = highest_profit_percentage
        self.running_price = running_price
        self.direction = direction
        self.user_id = user_id
        self.strategy = strategy
        self.atr_percentage = atr_percentage

def _map_trade(trade: database.models.Trade):
    return Trade(
        id = trade.id,
        symbol = trade.symbol,
        base_asset = trade.base_asset,
        base_asset_amount = trade.base_asset_amount,
        quote_asset = trade.quote_asset,
        quote_asset_amount = trade.quote_asset_amount,
        entry_price = trade.entry_price,
        entry_date = trade.entry_date,
        exit_price = trade.exit_price,
        exit_date = trade.exit_date,
        exit_reason = trade.exit_reason,
        profit_percentage = trade.profit_percentage,
        highest_profit_percentage = trade.highest_profit_percentage,
        running_price = trade.running_price,
        direction = trade.direction,
        user_id = trade.user_id,
        strategy = trade.strategy,
        atr_percentage = trade.atr_percentage,
    )

_USER_ID = 1

def is_already_trading(symbol: str, strategy: str) -> bool:
    deal = database.models.Trade.select().where(
        (database.models.Trade.symbol == symbol)
        & (database.models.Trade.exit_price.is_null(True))
        & (database.models.Trade.user_id == _USER_ID)
        & (database.models.Trade.strategy == strategy)
    )
    return bool(deal)

def get_all_active(strategy: str) -> List[Trade]:
    trades: List[database.models.Trade] = database.models.Trade.select().where(
       (database.models.Trade.exit_price.is_null(True))
        & (database.models.Trade.user_id == _USER_ID)
        & (database.models.Trade.strategy == strategy)
    )
    return list(map(_map_trade, trades))


def is_expired(trade: Trade) -> bool:
    return trade and (trade.entry_date + datetime.timedelta(hours=_EXPIRATION_PERIOD_HOURS)) > datetime.datetime.utcnow()


def is_trailing_stop(running_price: float, trade: Trade, trailing_stop_percentage = 1.0, trailing_start_percentage = 1.0) -> bool:
    # trailing activates only after current_profit_percentage is higher than trailing_start_percentage
    # meaning that we must be in profit for at least 1%
    current_profit_percentage = get_current_profit_percentage(running_price, trade)
    return (
        current_profit_percentage >= trailing_start_percentage and
        trade.highest_profit_percentage > current_profit_percentage and
        (trade.highest_profit_percentage - current_profit_percentage) >= trailing_stop_percentage
    )


def is_atr_stop_loss(running_price: float, trade: Trade) -> bool:
    current_profit_percentage = get_current_profit_percentage(running_price, trade)
    return current_profit_percentage <= -trade.atr_percentage


def is_greedy_profit_reached(running_price: float, trade: Trade, greedy_percentage = 1.0) -> bool:
    current_profit_percentage = get_current_profit_percentage(running_price, trade)
    return current_profit_percentage > greedy_percentage
    

def get_current_profit_percentage(running_price: float, trade: Trade) -> float:
    return (
        (running_price - trade.entry_price) / trade.entry_price * 100
        if trade.direction == TradeDirection.long.value
        else (trade.entry_price - running_price) / trade.entry_price * 100
    )


def enter(trade: Trade):
    database.models.Trade.create(
           base_asset = trade.base_asset,
           base_asset_amount = trade.base_asset_amount,
           quote_asset = trade.quote_asset,
           entry_price = trade.entry_price,
           running_price = trade.entry_price,
           direction = trade.direction.value, 
           user_id = _USER_ID,
           strategy = trade.strategy,
           atr_percentage = trade.atr_percentage,
        )
    

def exit(id: int, running_price: float, reason: str):
    query = database.models.Trade.update(
            exit_price = running_price,
            exit_reason = reason,
            exit_date =  datetime.datetime.utcnow(),
            running_price = running_price
        ).where(
            (database.models.Trade.id == id) 
            & (database.models.Trade.user_id == _USER_ID)
        )
    query.execute()
    

def extend(id: int, running_price: float):
    query = database.models.Trade.update(
            running_price =  running_price
        ).where(
            (database.models.Trade.id == id)
            & (database.models.Trade.user_id == _USER_ID)
        )
    query.execute()
