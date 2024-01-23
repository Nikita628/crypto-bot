import threading
import time
from bot.binance import BinanceInterval, fill_in_usdt_symbols, get_kline, get_all_usdt_symbols
from strategies import (
    Base,
    DualMomentum,
    DualMomentumCustomized,
    VolumeSurge,
)
from typing import List
from integration.telegram import consume_signals_queue
import os
import json
import asset


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
        greedy_profit_percentage=1,
        is_over_price_exit=True,
    ),

    DualMomentum(
        name='dual_momentum_trailing',
        trailing_stop_percentage=1,
        is_over_price_exit=True,
    ),

    DualMomentum(
        name='dual_momentum_lower_greedy',
        greedy_profit_percentage=1,
        is_lower_timeframe_confirmation=True,
        is_over_price_exit=True,
    ),

    # dual momentum customized ####################
    DualMomentumCustomized(
        name='dual_momentum_customized',
        is_over_price_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_greedy', 
        greedy_profit_percentage=1, 
        hard_stop_loss_percentage=-3,
        is_over_price_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing', 
        is_over_price_exit=True,
        trailing_stop_percentage=1,
        hard_stop_loss_percentage=-3,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_atr_limit', 
        is_over_price_exit=True,
        trailing_stop_percentage=1,
        hard_stop_loss_percentage=-3,
        atr_limit=8,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_volatility_limit', 
        is_over_price_exit=True,
        trailing_stop_percentage=1,
        hard_stop_loss_percentage=-3,
        volatility_limit=6,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_lower_greedy', 
        greedy_profit_percentage=1, 
        hard_stop_loss_percentage=-3,
        is_over_price_exit=True,
        is_lower_timeframe_confirmation=True,
    ),

    # volume surge ##############################
    VolumeSurge(), 
    VolumeSurge(
        name='volume_surge_greedy',
        greedy_profit_percentage=1,
    ),
    VolumeSurge(
        name='volume_surge_greedy_hard_stop',
        greedy_profit_percentage=1,
        hard_stop_loss_percentage=-3,
    ),
    VolumeSurge(
        name='volume_surge_greedy_hard_stop',
        greedy_profit_percentage=1,
        hard_stop_loss_percentage=-3,
        hold_period_hours=24,
    ),
    VolumeSurge(
        name='volume_surge_trailing',
        trailing_stop_percentage=1,
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
        
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    # TODO: switch to using websockets and async programming
    # asyncio.run(main_ws())
    try:
        start_bot()
    except Exception as e:
        print(f'error staring bot: {e}')
