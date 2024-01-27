from telegram import Bot
import os
import asyncio
from telegram.request import HTTPXRequest
import queue
import time
import datetime

_CRYPTO_BOT_TOKEN = os.environ.get('CRYPTO_BOT_TOKEN')
_CRYPTO_BOT_SIGNALS_CHAT_ID = os.environ.get('CRYPTO_BOT_SIGNALS_CHAT_ID')

if not _CRYPTO_BOT_TOKEN or not _CRYPTO_BOT_SIGNALS_CHAT_ID:
    raise ValueError('telegram bot env variables are not set')

_REQUEST = HTTPXRequest(
    connection_pool_size=20,
    read_timeout=30,
    write_timeout=30,
    connect_timeout=30,
    pool_timeout=30
)
_SIGNALS_QUEUE = queue.Queue()
# dual_momentum_crypto_bot
_TG_BOT = Bot(token=_CRYPTO_BOT_TOKEN, request=_REQUEST)

class TradeSignal:
    def __init__(
            self,
            strategy: str,
            symbol: str,
            running_price: float,
            is_long: bool = False,
        ):
        self.strategy = strategy
        self.symbol = symbol
        self.is_long = is_long
        self.date = f'\n{datetime.datetime.utcnow().strftime("%b %d, %Y %H:%M")}'
        self.running_price = running_price
        self.url = f'\nhttps://www.binance.com/en/trade/{symbol.replace("USDT", "")}_USDT'
   
class TradeEntrySignal(TradeSignal):
    def __init__(
            self,
            strategy: str,
            symbol: str,
            running_price: float,
            is_long: bool = False,
        ):
        super().__init__(strategy, symbol, running_price, is_long)
        self.is_long = is_long

    def __str__(self):
        direction = 'long' if self.is_long else 'short'
        result = f"{self.strategy}\n{self.symbol} entry {direction}"
        result += f'\nprice: {self.running_price} USDT'
        result += self.date
        result += self.url
        return result
    
class TradeExitSignal(TradeSignal):
    def __init__(
            self,
            strategy: str,
            symbol: str,
            running_price: float,
            exit_reason: str,
            profit_percentage: float,
            is_long: bool = False,
        ):
        super().__init__(strategy, symbol, running_price, is_long)
        self.exit_reason = exit_reason
        self.profit_percentage = profit_percentage

    def __str__(self):
        direction = 'long' if self.is_long else 'short'
        exit_reason = f'\nexit_reason: {self.exit_reason}'
        result = f"{self.strategy}\n{self.symbol} exit {direction}" 
        result += exit_reason
        result += f'\nprofit_percentage: {self.profit_percentage}'
        result += f'\nprice: {self.running_price} USDT'
        result += self.date
        result += self.url
        return result


async def _post_async(signal: TradeSignal):
    # trying to send a message several times with retries,
    # in case of a network error
    max_attempts = 10
    base_delay_between_attempts = 1

    for attempt in range(max_attempts):
        try:
            await _TG_BOT.send_message(chat_id=_CRYPTO_BOT_SIGNALS_CHAT_ID, text=str(signal))
            break
        except Exception as e:
            if attempt < max_attempts - 1:
                delay_between_attempts = base_delay_between_attempts * attempt
                time.sleep(delay_between_attempts)


def consume_signals_queue():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def consume():
        while True:
            signal = _SIGNALS_QUEUE.get()
            try:
                await loop.create_task(_post_async(signal))
                _SIGNALS_QUEUE.task_done()
            except Exception as e:
                print(f"Failed to consume signal: {signal}, error: {e}")
            time.sleep(5)

    loop.run_until_complete(consume())


def post(signal: TradeSignal):  
    _SIGNALS_QUEUE.put(signal)
