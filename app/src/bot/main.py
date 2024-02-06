import threading
import time
from bot.exchange.binance import BinanceInterval, fill_in_usdt_symbols, get_kline, get_all_usdt_symbols
from strategies import (
    Base,
    DualMomentum,
    DualMomentumCustomized,
    VolumeSurge,
    VolumeSurgeCustomized,
)
from typing import List
from integration.telegram import consume_signals_queue, consume_errors_queue
import os
import json
import bot.models.asset as asset
from bot.models.trade import ExitReason
import redis

""" r = redis.Redis(host="redis", port=6379, decode_responses=True)
d = r.set('foo', 'bar')
print(d)
v = r.get('foo')
print(v) """


# TODO: future websockets and async migration
# fetch 500 previous candlesticks over HTTP first,
# then receive real time updates for the current candlestick
#
# import asyncio
# import websockets
# import json
# async def subscribe_to_streams(websocket, pairs, interval):
#     # Prepare the subscription message for the required streams
#     streams = [f"{pair}@kline_{interval}" for pair in pairs]
#     subscribe_message = json.dumps({
#         "method": "SUBSCRIBE",
#         "params": streams,
#         "id": 1
#     })

#     # Send the subscription message
#     await websocket.send(subscribe_message)

#     # Listening for messages on the stream
#     while True:
#         response = await websocket.recv()
#         print(f"Received data: {response}")

# async def main_ws():
#     uri = "wss://stream.binance.com:9443/stream"
#     async with websockets.connect(uri) as websocket:
#         # Subscribe to 'btcusdt' and 'ethusdt' kline data streams
#         pairs = ["btcusdt", "ethusdt", "steemusdt"]
#         interval = "1d"  # Set the interval for kline data
#         await subscribe_to_streams(websocket, pairs, interval)




############### TODO: ######################################################
# API rate limits - 3000 req per min
#
# WEBSOCKETS rate limits - approx 300 connections per attempt per 5 min, 
# 5 messages per sec per connection,
# 1024 streams per connection
#
# logging
# beware of delisting
# beware of 'dangerous' coins

strategies: List[Base] = [
    # dual momentum ############################
    DualMomentum(
        name='dual_momentum_greedy',
        greedy_profit_percentage=0.5,
        hard_stop_loss_percentage=-3,
        is_over_price_exit=True,
    ),

    DualMomentum(
        name='dual_momentum_trailing',
        trailing_stop_percentage=0.5,
        hard_stop_loss_percentage=-3,
        is_over_price_exit=True,
    ),

    DualMomentum(
        name='dual_momentum_trailing_no_hard_stop',
        trailing_stop_percentage=0.5,
    ),

    # dual momentum customized ####################
    DualMomentumCustomized(
        name='dual_momentum_customized',
        is_over_price_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_greedy', 
        greedy_profit_percentage=0.5, 
        hard_stop_loss_percentage=-3,
        is_over_price_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing', 
        is_over_price_exit=True,
        trailing_stop_percentage=0.5,
        hard_stop_loss_percentage=-3,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing_no_hard_stop', 
        is_over_price_exit=True,
        trailing_stop_percentage=0.5,
    ),

    # volume surge ##############################
    VolumeSurge(
        name='volume_surge_trailing',
        trailing_stop_percentage=0.5,
    ),
    VolumeSurge(
        timeframe=BinanceInterval.h4,
        name='volume_surge_greedy_hard_stop_4h',
        greedy_profit_percentage=0.5,
        hard_stop_loss_percentage=-3,
        pvt_range_percentage=2,
        pvt_surge_percentage=2.5,
        pvt_range_loockback=6,
    ),
    VolumeSurge(
        name='volume_surge_greedy_hard_stop_hold_24',
        greedy_profit_percentage=1,
        hard_stop_loss_percentage=-3,
        hold_period_hours=24,
        hold_exit_reason={ExitReason.long_exit, ExitReason.short_exit}
    ),
    VolumeSurge(
        name='volume_surge_greedy_hard_stop_4h_1.5',
        timeframe=BinanceInterval.h4,
        greedy_profit_percentage=0.5,
        hard_stop_loss_percentage=-3,
        pvt_range_percentage=1,
        pvt_surge_percentage=1.3,
        pvt_range_loockback=6,
    ),
    VolumeSurge(
        name='volume_surge_greedy_hard_stop_1h_2',
        timeframe=BinanceInterval.h1,
        greedy_profit_percentage=0.2,
        hard_stop_loss_percentage=-2,
        pvt_range_percentage=1,
        pvt_surge_percentage=2,
        pvt_range_loockback=10,
    ),
    VolumeSurgeCustomized(
        name='volume_surge_customized_5min',
        timeframe=BinanceInterval.min5,
        greedy_profit_percentage=0.2,
        hard_stop_loss_percentage=-2,
        pvt_range_loockback=12,
        pvt_surge_multiplier=3,
    ),
    VolumeSurgeCustomized(
        name='volume_surge_customized_4h',
        timeframe=BinanceInterval.h4,
        greedy_profit_percentage=0.2,
        hard_stop_loss_percentage=-2,
        pvt_range_loockback=6,
        pvt_surge_multiplier=2,
    ),
    VolumeSurgeCustomized(
        name='volume_surge_customized_4h_lower_confirmation',
        timeframe=BinanceInterval.h4,
        greedy_profit_percentage=0.2,
        hard_stop_loss_percentage=-4,
        pvt_range_loockback=6,
        pvt_surge_multiplier=2,
        is_lower_timeframe_confirmation=True,
    ),
    VolumeSurgeCustomized(
        name='volume_surge_customized_1d',
        greedy_profit_percentage=1,
        hard_stop_loss_percentage=-3,
        pvt_surge_multiplier=2,
    ),
    VolumeSurgeCustomized(
        name='volume_surge_customized_trailing_4h',
        timeframe=BinanceInterval.h4,
        trailing_stop_percentage=0.2,
        hard_stop_loss_percentage=-2,
        pvt_range_loockback=6,
        pvt_surge_multiplier=2,
    ),
    VolumeSurgeCustomized(
        name='volume_surge_customized_trailing_4h_lower_confirmation',
        timeframe=BinanceInterval.h4,
        trailing_stop_percentage=0.2,
        hard_stop_loss_percentage=-4,
        pvt_range_loockback=6,
        pvt_surge_multiplier=2,
        is_lower_timeframe_confirmation=True,
    ),
]

def run_test():
    usdt_symbols = get_all_usdt_symbols()
    not_volatile_symbols = []
    for symbol in usdt_symbols:
        kline = get_kline(symbol, BinanceInterval.day, 501)
        kline.add_atr()
        current_atr = kline.df['atr'].iloc[-1]
        current_close = kline.df['close'].iloc[-1]
        atr_percentage = current_atr / current_close * 100
        if atr_percentage < 8:
            not_volatile_symbols.append(symbol)
        time.sleep(1)
    return not_volatile_symbols

def start_bot():
    fill_in_usdt_symbols()

    # symbols = run_test()
    # with open('low_atr_symbols.json', 'w') as file:
    #     json.dump(symbols, file) 
    
    threads: List[threading.Thread] = []

    for strategy in strategies:
        # create assets if need
        if not asset.is_exists(coin = 'USDT', strategy = strategy.strategy):
            new_asset = asset.Asset(
                strategy=strategy.strategy,
            )
            asset.create_test_instance(new_asset)

        buy_thread = threading.Thread(target=strategy.search_entry)
        sell_thread = threading.Thread(target=strategy.search_exit)
        threads.append(buy_thread)
        threads.append(sell_thread)
        buy_thread.start()
        sell_thread.start()
    
    if os.environ.get('NEED_TO_POST_SIGNALS_IN_TG') == 'true':
        tg_bot_signals_consumer = threading.Thread(target=consume_signals_queue)
        threads.append(tg_bot_signals_consumer)
        tg_bot_signals_consumer.start()

    if os.environ.get('NEED_TO_POST_STATUS_IN_TG') == 'true':
        tg_bot_errors_consumer = threading.Thread(target=consume_errors_queue)
        threads.append(tg_bot_errors_consumer)
        tg_bot_errors_consumer.start()
    
    
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    # TODO: switch to using websockets and async programming
    # asyncio.run(main_ws())
    try:
        start_bot()
    except Exception as e:
        print(f'error staring bot: {e}')
