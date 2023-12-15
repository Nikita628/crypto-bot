import threading
from dual_momentum import search_entry, search_exit



############### TODO: ######################################################
# API rate limits - 3000 req per min
# logging
# error handling global
# class models for DataFrame shape, for csv file shape
# beware of delisting
# beware of 'dangerous' coins
# make sure only one instance of a coin is bought a time

def main():
    buy_thread = threading.Thread(target=search_entry)
    sell_thread = threading.Thread(target=search_exit)

    buy_thread.start()
    sell_thread.start()

    buy_thread.join()
    sell_thread.join()

    # df = fetch_binance_data('BTCUSDT', '1d', 501)

    # add_gmma(df)
    # add_rsi(df)
    # add_stoch_osc(df, 5, 3, 2, 'short')
    # add_stoch_osc(df, 20, 3, 8, 'long')
    # add_volume_sma(df)
    # add_200ema(df)

    # print('before last -----------', df.iloc[-2])
    # print('last ------------------', df.iloc[-1])

if __name__ == "__main__":
    main()

