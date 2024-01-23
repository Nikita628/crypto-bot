from enum import Enum
import datetime
import database.models

_USER_ID = 1
_START_AMOUNT = 1000 # 1000 USDT, for example
_PORTION_PER_TRADE = 0.1 # 10%
_AMOUNT_PER_TRADE = _START_AMOUNT*_PORTION_PER_TRADE

class AssetConstants(float, Enum):
    start_amount = _START_AMOUNT
    portion_per_trade = _PORTION_PER_TRADE
    amount_per_trade = _AMOUNT_PER_TRADE

class Asset:
    def __init__(
            self,
            id: int = None,
            coin: str = None,
            amount: float = None,
            strategy: str = None,
            user_id: int = None,
        ):
        self.id = id
        self.coin = coin
        self.amount = amount
        self.strategy = strategy
        self.user_id = user_id

def get_amount(coin: str, strategy: str):
    asset = database.models.Asset.get(
        database.models.Asset.coin == coin,
        database.models.Asset.strategy == strategy,
        database.models.Asset.user_id == _USER_ID
    )
    if bool(asset):
        return asset.amount
    else:
        return false


def is_exists(coin: str, strategy: str) -> bool:
    asset = database.models.Asset.select().where(
        (database.models.Asset.coin == coin)
        & (database.models.Asset.strategy == strategy)
        & (database.models.Asset.user_id == _USER_ID)
    )
    return bool(asset)

def create(asset: Asset):
    database.models.Asset.create(
           coin = asset.coin,
           amount = asset.amount,
           strategy = asset.strategy,
           user_id = _USER_ID,
        )

def create_test_instance(asset: Asset):
    database.models.Asset.create(
           coin = 'USDT',
           amount = AssetConstants.start_amount,
           strategy = asset.strategy,
           user_id = _USER_ID,
        )
     
def update_amount(amount: float, coin: str, strategy: str):
    query = database.models.Asset.update(
            amount = amount
        ).where(
            (database.models.Asset.coin == coin) 
            & (database.models.Asset.strategy == strategy)
            & (database.models.Asset.user_id == _USER_ID)
        )
    query.execute()