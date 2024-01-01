from telegram import Bot
import os
import asyncio
from telegram.request import HTTPXRequest
import queue
import time
import datetime

_DUAL_MOMENTUM_CRYPTO_BOT_TOKEN = os.environ.get('DUAL_MOMENTUM_CRYPTO_BOT_TOKEN')
_CRYPTO_BOT_SIGNALS_CHANNEL_ID = os.environ.get('CRYPTO_BOT_SIGNALS_CHANNEL_ID')

if not _DUAL_MOMENTUM_CRYPTO_BOT_TOKEN or not _CRYPTO_BOT_SIGNALS_CHANNEL_ID:
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
_DUAL_MOMENTUM_TG_BOT = Bot(token=_DUAL_MOMENTUM_CRYPTO_BOT_TOKEN, request=_REQUEST)

class TradeSignal:
    def __init__(
            self,
            strategy: str,
            symbol: str,
            is_entry: bool = False,
            is_long: bool = False,
            exit_reason: str = None,
        ):
        self.strategy = strategy
        self.symbol = symbol
        self.is_long = is_long
        self.is_entry = is_entry
        self.exit_reason = exit_reason

    def __str__(self):
        direction = '\ndirection: long' if self.is_long else 'direction: short' if self.is_entry else ''
        date = f'\ndate: {datetime.datetime.utcnow().strftime("%b %d, %Y %H:%M")}'
        exit_reason = f'\nexit_reason: {self.exit_reason}' if not self.is_entry else ''
        result = f"signal: {'entry' if self.is_entry else 'exit'}\nstrategy: {self.strategy}\nsymbol: {self.symbol}"
        if direction:
            result += direction
        if exit_reason:
            result += exit_reason
        result += date
        return result

async def _post_signal_async(signal: TradeSignal):
    # trying to send a message several times with retries,
    # in case of a network error
    max_attempts = 30
    base_delay_between_attempts = 2

    for attempt in range(max_attempts):
        try:
            await _DUAL_MOMENTUM_TG_BOT.send_message(chat_id=_CRYPTO_BOT_SIGNALS_CHANNEL_ID, text=str(signal))
            break
        except Exception as e:
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


def post_signal(signal: TradeSignal):  
    _SIGNALS_QUEUE.put(signal)
