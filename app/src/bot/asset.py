from enum import Enum
import datetime
import database.models

_USER_ID = 1
_START_USDT_AMOUNT = 1000 # 1000 USDT, for example
_PER_TRADE_PORTION = 0.1 # 10%
_PER_TRADE_USDT_AMOUNT = _START_USDT_AMOUNT*_PER_TRADE_PORTION

class AssetConstants(float, Enum):
    start_usdt_amount = _START_USDT_AMOUNT
    per_trade_portion = _PER_TRADE_PORTION
    per_trade_ustd_amount = _PER_TRADE_USDT_AMOUNT

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

def get_amount(coin: str, strategy: str) -> float:
    asset = database.models.Asset.get(
        database.models.Asset.coin == coin,
        database.models.Asset.strategy == strategy,
        database.models.Asset.user_id == _USER_ID
    )
    if bool(asset):
        return asset.amount
    else:
        return 0


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
           amount = AssetConstants.start_usdt_amount,
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