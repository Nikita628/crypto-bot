import datetime
import psycopg2
from enum import Enum
##########################################
#
# one of the assets will be USDT, not for trading
#
# tables in DB: asset, suspended_symbol(suspention_start, symbol)
#
##########################################

MAX_ASSETS_AMOUNT = 10
EXPIRATION_PERIOD_HOURS = 48
TRAILING_STOP_PERCENTAGE = -1

class TradeDirection(Enum):
    long = 'long'
    short = 'short'

class Asset:
    def __init__(
            self, 
            symbol: str, 
            entry_price: float,
            entry_date: datetime.datetime,
            current_profit_percentage: float,
            direction: TradeDirection,
            amount: float
        ):
        self.symbol = symbol
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.amount = amount
        self.current_profit_percentage = current_profit_percentage
        self.direction = direction


def buy(asset):
    return 1

# buy(asset)
# check if limit, rebalance if needed
# subtract amount from USDT
# add asset to DB


# sell(asset)
# convert to USDT
# remove from DB


# is_asset(symbol: str) -> bool:
# check if symbol is asset


# get_assets() -> List[Asset]:
# return all assets except USDT


# is_expired(asset) -> bool:
# if (now - asset.entry_date) > EXPIRATION_PERIOD and profit_percentage is +- 0.5
# then expired


# is_trailing_stop_hit(asset, new_profit_percentage) -> bool:
# if new_profit_percentage < TRAILING_STOP or (new_profit_perc - curr_prof_perc) < TRAILING_STOP
# then hit


# suspend(symbol):
# table in DB for this ?
# suspention_start, symbol
#
# suspention means we do not trade the asset
# reasons - it is expired and we just sold it,
# trailing stop just hit


# rebalance():
# after we hit trailing stop or expired
# we sell the asset, and buy another one