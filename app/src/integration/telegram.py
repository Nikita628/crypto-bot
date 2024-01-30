from telegram import Bot
import os
import asyncio
from telegram.request import HTTPXRequest
import queue
import time
import datetime

_CRYPTO_BOT_TOKEN = os.environ.get('CRYPTO_BOT_TOKEN')
_CRYPTO_BOT_SIGNALS_CHAT_ID = os.environ.get('CRYPTO_BOT_SIGNALS_CHAT_ID')
_CRYPTO_BOT_STATUS_CHAT_ID = os.environ.get('CRYPTO_BOT_STATUS_CHAT_ID')

if (not _CRYPTO_BOT_TOKEN 
    or not _CRYPTO_BOT_SIGNALS_CHAT_ID
    or not _CRYPTO_BOT_STATUS_CHAT_ID):
    raise ValueError('telegram bot env variables are not set')

_REQUEST = HTTPXRequest(
    connection_pool_size=20,
    read_timeout=30,
    write_timeout=30,
    connect_timeout=30,
    pool_timeout=30
)
_SIGNALS_QUEUE = queue.Queue()
_ERRORS_QUEUE = queue.Queue()
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
        self.direction = 'long' if is_long else 'short'
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
        result = f"{self.strategy}\n{self.symbol} entry {self.direction}"
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
            entry_price: float,
            exit_reason: str,
            profit_percentage: float,
            is_long: bool = False,
        ):
        super().__init__(strategy, symbol, running_price, is_long)
        self.exit_reason = exit_reason
        self.profit_percentage = profit_percentage
        self.entry_price = entry_price

    def __str__(self):
        result = f"{self.strategy}\n{self.symbol} exit {self.direction}" 
        result += f'\nentry price: {self.entry_price} USDT'
        result += f'\nexit price: {self.running_price} USDT'
        result += f'\nprofit_percentage: {self.profit_percentage}'
        result += f'\nexit_reason: {self.exit_reason}'
        result += self.date
        result += self.url
        return result


async def _post_signal_async(signal: TradeSignal):
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


async def _post_error_async(error_msg: str):
    # trying to send a message several times with retries,
    # in case of a network error
    max_attempts = 10
    base_delay_between_attempts = 1

    for attempt in range(max_attempts):
        try:
            await _TG_BOT.send_message(chat_id=_CRYPTO_BOT_STATUS_CHAT_ID, text=error_msg)
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
                await loop.create_task(_post_signal_async(signal))
                _SIGNALS_QUEUE.task_done()
            except Exception as e:
                print(f"Failed to consume signal: {signal}, error: {e}")
            time.sleep(5)

    loop.run_until_complete(consume())


def consume_errors_queue():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def consume():
        while True:
            error_msg = _ERRORS_QUEUE.get()
            try:
                await loop.create_task(_post_error_async(error_msg))
                _ERRORS_QUEUE.task_done()
            except Exception as e:
                print(f"Failed to consume error: {error_msg}, error: {e}")
            time.sleep(5)

    loop.run_until_complete(consume())


def post_signal(signal: TradeSignal):  
    _SIGNALS_QUEUE.put(signal)

def post_error(error_msg: str):  
    _ERRORS_QUEUE.put(error_msg)
