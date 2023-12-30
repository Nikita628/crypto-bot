import threading
from bot.binance import BinanceInterval
from strategies import (
    Base,
    DualMomentum,
    DualMomentumCustomized,
    VolumeSurge,
)
from typing import List

############### TODO: ######################################################
# API rate limits - 3000 req per min
# logging
# beware of delisting
# beware of 'dangerous' coins

strategies: List[Base] = [
    DualMomentum(), 
    DualMomentum(timeframe=BinanceInterval.h12, name='dual_momentum_12_h'),
    DualMomentumCustomized(name='trailing_stop', is_trailing_stop_enabled=True),
    DualMomentumCustomized(timeframe=BinanceInterval.h12, name='trailing_stop_12_h', is_trailing_stop_enabled=True),
    VolumeSurge(),
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

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    start_bot()
