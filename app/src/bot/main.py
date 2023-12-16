import threading
from .technical_indicators import PandasMixin
from dual_momentum import search_entry, search_exit
import pandas as pd

@pd.api.extensions.register_dataframe_accessor("custom")
def _custom_accessor(pandas_obj):
    return PandasMixin(pandas_obj)


# TODO: incorporate latest changes from main branch:
# new tech indicators - pvt, mfi
# trailing stop (needs modifications)
# overbought, oversold


############### TODO: ######################################################
# API rate limits - 3000 req per min
# logging
# error handling global
# beware of delisting
# beware of 'dangerous' coins
def start_bot():
    print('starting bot...')

    buy_thread = threading.Thread(target=search_entry)
    sell_thread = threading.Thread(target=search_exit)

    buy_thread.start()
    sell_thread.start()

    buy_thread.join()
    sell_thread.join()

if __name__ == "__main__":
    start_bot()
