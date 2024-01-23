import datetime
import database.models

# end_time = datetime.datetime.utcnow() + datetime.timedelta(hours=hold_period_hours)

_USER_ID = 1

class Hold:
    def __init__(
            self,
            id: int = None,
            symbol: str = None,
            strategy: str = None,
            start_time: datetime.datetime = None,
            end_time: datetime.datetime or None = None,
            user_id: int = None,
        ):
        self.id = id
        self.symbol = symbol
        self.strategy = strategy
        self.start_time = start_time
        self.end_time = end_time
        self.user_id = user_id
        

def is_active(symbol: str, strategy: str):
    hold = database.models.Hold.select().where(
        (database.models.Hold.end_time > datetime.datetime.utcnow())
        & (database.models.Hold.symbol == symbol)
        & (database.models.Hold.strategy == strategy)
        & (database.models.Hold.user_id == _USER_ID)
    )
    return bool(hold)

def add(hold: Hold):
    database.models.Hold.create(
           symbol = hold.symbol,
           strategy = hold.strategy,
           end_time = hold.end_time,
           user_id = _USER_ID,
        )