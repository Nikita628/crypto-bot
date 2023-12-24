import threading
from strategies import (
    Base,
    DualMomentum,
    DualMomentumLowerTimeframe,
)
from typing import List

# TODO: incorporate latest changes from main branch:
# trailing stop (needs modifications)
# overbought, oversold

# add logging to file, one logger per strategy

############### TODO: ######################################################
# API rate limits - 3000 req per min
# logging
# error handling global
# beware of delisting
# beware of 'dangerous' coins

strategies: List[Base] = [DualMomentum(), DualMomentumLowerTimeframe()]

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
