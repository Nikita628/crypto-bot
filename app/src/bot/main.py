import threading
import time
from bot.exchange.binance import BinanceInterval, cache_usdt_symbols_list, get_kline, get_all_usdt_symbols
from strategies import (
    IndicatorSettings,
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
        is_atr_stop_loss_exit=True,
    ),

    DualMomentum(
        name='dual_momentum_trailing_small_stoch_and_rsi_overprice_confirmation',
        is_stoch_and_rsi_exit=True,
        trailing_start_percentage=0.5,
        trailing_stop_percentage=0.5,
        is_over_price_exit=True,
        confirmation_timeframe=BinanceInterval.week,
    ),

    DualMomentum(
        name='dual_momentum_trailing_small_stoch_and_rsi_overprice_lookback',
        is_stoch_and_rsi_exit=True,
        trailing_start_percentage=0.5,
        trailing_stop_percentage=0.5,
        is_over_price_exit=True,
        indicator_settings=IndicatorSettings(
            ema_200_downward_lookback=30,
            ema_200_upward_lookback=30,
            long_gmma_above_200_ema_lookback=7,
            long_gmma_below_200_ema_lookback=7,
            long_gmma_downward_lookback=5,
            long_gmma_upward_lookback=5,
            short_gmma_above_long_gmma_lookback=7,
            short_gmma_below_long_gmma_lookback=7,
            short_gmma_downward_lookback=2,
            short_gmma_upward_lookback=2,
        ),
    ),

    DualMomentum(
        name='dual_momentum_greedy_no_hard_stop',
        is_atr_stop_loss_exit=True,
        greedy_profit_percentage=0.5,
    ),

    DualMomentum(
        name='dual_momentum_trailing',
        trailing_stop_percentage=0.5,
        hard_stop_loss_percentage=-3,
        is_over_price_exit=True,
        is_atr_stop_loss_exit=True,
    ),

    DualMomentum(
        name='dual_momentum_trailing_no_hard_stop',
        trailing_stop_percentage=0.5,
        is_atr_stop_loss_exit=True,
    ),

    DualMomentum(
        name='dual_momentum_trailing_small',
        trailing_stop_percentage=0.2,
        trailing_start_percentage=0.3,
        is_atr_stop_loss_exit=True,
    ),

    DualMomentum(
        name='dual_momentum_trailing_0.5_stop_atr_0.7',
        trailing_stop_percentage=0.2,
        trailing_start_percentage=0.5,
        stop_loss_atr_percentage=0.7,
        is_atr_stop_loss_exit=True,
    ),

    DualMomentum(
        name='dual_momentum_trailing_stoch_and_rsi',
        trailing_stop_percentage=0.5,
        is_stoch_and_rsi_exit=True,
    ),

    DualMomentum(
        name='dual_momentum_trailing_stoch_or_rsi',
        trailing_stop_percentage=0.5,
    ),

    DualMomentum(
        name='dual_momentum_trailing_small_stoch_or_rsi',
        trailing_start_percentage=0.5,
        trailing_stop_percentage=0.25,
    ),

    DualMomentum(
        name='dual_momentum_trailing_small_stoch_and_rsi',
        is_stoch_and_rsi_exit=True,
        trailing_start_percentage=0.5,
        trailing_stop_percentage=0.25,
    ),

    DualMomentum(
        name='dual_momentum_trailing_small_stoch_or_rsi_overprice',
        trailing_start_percentage=0.5,
        trailing_stop_percentage=0.25,
        is_over_price_exit=True,
    ),

    DualMomentum(
        name='dual_momentum_trailing_small_stoch_and_rsi_overprice',
        is_stoch_and_rsi_exit=True,
        trailing_start_percentage=0.5,
        trailing_stop_percentage=0.25,
        is_over_price_exit=True,
    ),

    DualMomentum(
        name='dual_momentum_trailing_small_stoch_or_rsi_hold_24',
        trailing_start_percentage=0.5,
        trailing_stop_percentage=0.25,
        hold_period_hours=24,
        hold_exit_reason={ExitReason.trailing_stop},
    ),

    DualMomentum(
        name='dual_momentum_plain_stoch_or_rsi',
    ),

    DualMomentum(
        name='dual_momentum_plain_stoch_and_rsi',
        is_stoch_and_rsi_exit=True,
    ),

    # dual momentum customized ####################
    DualMomentumCustomized(
        name='dual_momentum_customized',
        is_over_price_exit=True,
        is_atr_stop_loss_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_greedy_xs', 
        greedy_profit_percentage=0.1, 
        hard_stop_loss_percentage=-5,
        is_over_price_exit=True,
        is_atr_stop_loss_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing', 
        is_over_price_exit=True,
        trailing_stop_percentage=0.5,
        hard_stop_loss_percentage=-3,
        is_atr_stop_loss_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing_small',
        trailing_stop_percentage=0.1,
        trailing_start_percentage=0.5,
        is_atr_stop_loss_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing_no_hard_stop', 
        is_over_price_exit=True,
        trailing_stop_percentage=0.5,
        is_atr_stop_loss_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing_no_hard_stop_no_overprice', 
        trailing_stop_percentage=0.5,
        is_atr_stop_loss_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing_stoch_or_rsi', 
        trailing_stop_percentage=0.5,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing_stoch_and_rsi', 
        trailing_stop_percentage=0.5,
        is_stoch_and_rsi_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing_stoch_or_rsi_overprice', 
        trailing_stop_percentage=0.5,
        is_over_price_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing_stoch_and_rsi_overprice', 
        trailing_stop_percentage=0.5,
        is_stoch_and_rsi_exit=True,
        is_over_price_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing_small_stoch_or_rsi', 
        trailing_stop_percentage=0.5,
        trailing_start_percentage=0.5,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_plain_stoch_or_rsi',
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_plain_stoch_and_rsi',
        is_stoch_and_rsi_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing_xs_stoch_or_rsi_overprice', 
        trailing_stop_percentage=0.25,
        trailing_start_percentage=0.25,
        is_over_price_exit=True,
    ),

    DualMomentumCustomized(
        name='dual_momentum_customized_trailing_xs_stoch_and_rsi_overprice', 
        trailing_stop_percentage=0.25,
        trailing_start_percentage=0.25,
        is_over_price_exit=True,
        is_stoch_and_rsi_exit=True,
    ),

    # volume surge ##############################
    # VolumeSurge(
    #     name='volume_surge_greedy_hard_stop_4h_1.5',
    #     timeframe=BinanceInterval.h4,
    #     greedy_profit_percentage=0.5,
    #     hard_stop_loss_percentage=-3,
    #     pvt_range_percentage=1,
    #     pvt_surge_percentage=1.3,
    #     pvt_range_loockback=6,
    # ),
    # VolumeSurgeCustomized(
    #     name='volume_surge_customized_4h',
    #     timeframe=BinanceInterval.h4,
    #     greedy_profit_percentage=0.2,
    #     hard_stop_loss_percentage=-2,
    #     pvt_range_loockback=6,
    #     pvt_surge_multiplier=2,
    # ),
]

def start_bot():
    print('caching usdt symbols...')
    cache_usdt_symbols_list()
    print('cached usdt symbols')
 
    threads: List[threading.Thread] = []

    for strategy in strategies:
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
