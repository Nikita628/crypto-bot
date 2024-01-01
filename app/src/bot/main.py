import threading
from bot.binance import BinanceInterval
from strategies import (
    Base,
    DualMomentum,
    DualMomentumCustomized,
    VolumeSurge,
)
from typing import List
from integration.telegram import consume_signals_queue
import os

############### TODO: ######################################################
# API rate limits - 3000 req per min
# logging
# beware of delisting
# beware of 'dangerous' coins

strategies: List[Base] = [
    # dual momentum
    DualMomentum(), 
    DualMomentum(name='dual_momentum_greedy', greedy_profit_percentage=1), 
    DualMomentum(name='dual_momentum_trailing', trailing_stop_percentage=1),
    DualMomentum(name='dual_momentum_trailing_greedy', trailing_stop_percentage=1, greedy_profit_percentage=1),

    DualMomentum(timeframe=BinanceInterval.h12, name='dual_momentum_12h'), 
    DualMomentum(timeframe=BinanceInterval.h12, name='dual_momentum_greedy_12h', greedy_profit_percentage=1), 
    DualMomentum(timeframe=BinanceInterval.h12, name='dual_momentum_trailing_12h', trailing_stop_percentage=1),
    DualMomentum(timeframe=BinanceInterval.h12, name='dual_momentum_trailing_greedy_12h', trailing_stop_percentage=1, greedy_profit_percentage=1),

    # dual momentum customized
    DualMomentumCustomized(), 
    DualMomentumCustomized(name='dual_momentum_customized_greedy', greedy_profit_percentage=1), 
    DualMomentumCustomized(name='dual_momentum_customized_trailing', trailing_stop_percentage=1),
    DualMomentumCustomized(name='dual_momentum_customized_trailing_greedy', trailing_stop_percentage=1, greedy_profit_percentage=1),

    DualMomentumCustomized(timeframe=BinanceInterval.h12, name='dual_momentum_customized_12h'), 
    DualMomentumCustomized(timeframe=BinanceInterval.h12, name='dual_momentum_customized_greedy_12h', greedy_profit_percentage=1), 
    DualMomentumCustomized(timeframe=BinanceInterval.h12, name='dual_momentum_customized_trailing_12h', trailing_stop_percentage=1),
    DualMomentumCustomized(timeframe=BinanceInterval.h12, name='dual_momentum_customized_trailing_greedy_12h', trailing_stop_percentage=1, greedy_profit_percentage=1),

    # volume surge
    VolumeSurge(), 
    VolumeSurge(name='volume_surge_greedy', greedy_profit_percentage=1), 
    VolumeSurge(name='volume_surge_trailing', trailing_stop_percentage=1),
    VolumeSurge(name='volume_surge_trailing_greedy', trailing_stop_percentage=1, greedy_profit_percentage=1),

    VolumeSurge(timeframe=BinanceInterval.h12, name='volume_surge_12h'), 
    VolumeSurge(timeframe=BinanceInterval.h12, name='volume_surge_greedy_12h', greedy_profit_percentage=1), 
    VolumeSurge(timeframe=BinanceInterval.h12, name='volume_surge_trailing_12h', trailing_stop_percentage=1),
    VolumeSurge(timeframe=BinanceInterval.h12, name='volume_surge_trailing_greedy_12h', trailing_stop_percentage=1, greedy_profit_percentage=1),
]

def start_bot():
    threads: List[threading.Thread] = []

    for strategy in strategies:
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
    try:
        start_bot()
    except Exception as e:
        print(f'error staring bot: {e}')
