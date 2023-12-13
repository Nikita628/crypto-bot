import pandas as pd
import core
import database.models

from technical_indicators import (
    add_200ema,
    add_gmma,
    add_rsi,
    add_stoch_osc,
    add_volume_sma
)
from binance import BinanceInterval, get_all_usdt_symbols, get_kline
from transaction import (
    Deal,
    DealDirection, 
    get_open_deals, 
    create_deal,
    is_expired, 
    is_symbol_in_open_deal,
    update_deal,
    exit_deal,
    is_trailing_stop_hit
)
import datetime
import time

LOOCKBACK = 501 # need 501 for proper calculation of EMA according to Binance
INTERVAL = BinanceInterval.day


def search_entry():
    try:
        usdt_symbols = sorted(get_all_usdt_symbols())

        while True:
            print(f'searching entry...')
            checked_symbols = 0
            
            for symbol in usdt_symbols:
                checked_symbols += 1
                try:
                    if checked_symbols % 10 == 0:
                        print(f'searched {checked_symbols} symbols...')

                    # current pair(symbol) is already in deal
                    if is_symbol_in_open_deal(symbol, 1):
                        continue

                    df = get_kline(symbol, INTERVAL, LOOCKBACK)
                    """ print(df) """

                    if len(df) < LOOCKBACK:
                        continue
            
                    add_gmma(df)
                    add_200ema(df)
                    add_rsi(df)
                    add_volume_sma(df)
                    add_stoch_osc(df, 5, 3, 2, 'short')
                    add_stoch_osc(df, 20, 3, 8, 'long')
                    is_long = is_long_entry(df)
                    is_short = is_short_entry(df)

                    if is_long or is_short:
                        print(f'going {DealDirection.long.value if is_long else DealDirection.short.value} - {symbol}')

                        deal = Deal(
                            base_asset=symbol.replace('USDT', ''),
                            quote_asset='USDT',
                            entry_price=df['close'].iloc[-1],
                            entry_date=datetime.datetime.utcnow(),
                            direction=DealDirection.long if is_long else DealDirection.short,
                            exit_price=None,
                            exit_date=None,
                            profit_percentage=0,
                            running_profit_percentage=0,
                            running_price=0,
                            user_id=1
                        )
                        create_deal(deal)
                
                except Exception as e:
                    print(f"Failed to process data for {symbol}: {e}")
                    
                time.sleep(2)
                
            time.sleep(300) # 5 minutes
    except:
        print(f"search_entry error")


def search_exit():
    try:
        while True:
            print(f'searching exit...')

            # get open deals for current user by iser_id
            open_deals = get_open_deals(1)

            for deal in open_deals:
                try:
                    df = get_kline(deal.symbol, INTERVAL, LOOCKBACK)
                    add_rsi(df)
                    add_stoch_osc(df, 5, 3, 2, 'short')
                    add_stoch_osc(df, 20, 3, 8, 'long')
                    trade_direction = deal.direction

                    if trade_direction == DealDirection.long.value and is_long_exit(df):
                        # sell(asset)
                        print(f'exiting long - {deal.symbol}')
                        exit_price = df['close'].iloc[-1]
                        exit_date =  datetime.datetime.utcnow()
                        profit = df['close'].iloc[-1] - float(deal.entry_price)
                        profit_percentage = profit * 100 / float(deal.entry_price)
                        print(profit_percentage)
                        exit_deal(exit_price, exit_date, profit_percentage, deal.symbol, 1)
                    
                    elif trade_direction == DealDirection.short.value and is_short_exit(df):
                        print(f'exiting short - {deal.symbol}')
                        exit_price = df['close'].iloc[-1]
                        exit_date =  datetime.datetime.utcnow()
                        profit = float(deal.entry_price) - df['close'].iloc[-1]
                        profit_percentage = profit * 100 / float(deal.entry_price)
                        exit_deal(exit_price, exit_date, profit_percentage, deal.symbol, 1)
                    
                    elif is_expired(deal):
                        print('expired transaction')
                        # sell and rebalance
                    
                    elif is_trailing_stop_hit():
                        # sell and rebalance
                        print('trailing stop hit')
                    
                    else:
                        profit = (
                            df['close'].iloc[-1] - float(deal.entry_price) 
                            if trade_direction == DealDirection.long.value
                            else float(deal.entry_price) - df['close'].iloc[-1]
                        )
                        running_profit_percentage = profit * 100 / float(deal.entry_price)
                        running_price =  df['close'].iloc[-1]
                        update_deal(running_profit_percentage, running_price, deal.symbol, 1)

                except Exception as e:
                    print(f"Failed to process data for {deal.symbol}: {e}")

            time.sleep(300)  # 5 minutes
    except:
        print(f"search_exit error")



def is_short_entry(df: pd.DataFrame):
    is_200ema_downward = df['ema_200'].iloc[-1] < df['ema_200'].iloc[-2]

    #### long term GMMA ######################
    long_term_emas = [30, 35, 40, 45, 50, 60]
    is_long_gmma_below_200ema = df[f'long_ema_{60}'].iloc[-1] < df['ema_200'].iloc[-1]
    is_long_gmma_downward = all(
        (df[f'long_ema_{ema}'].iloc[-1] < df[f'long_ema_{ema}'].iloc[-2]) 
        for ema in long_term_emas
    )
    is_long_gmma_separation = True
    for i in range(0, len(long_term_emas) - 1):
        if df[f'long_ema_{long_term_emas[i]}'].iloc[-1] >= df[f'long_ema_{long_term_emas[i + 1]}'].iloc[-1]:
            is_long_gmma_separation = False
            break

    #### short term GMMA #######################
    short_term_emas = [3, 5, 8, 10, 12, 15]
    is_short_term_GMMA_below_long_term_GMMA = df[f'short_ema_{15}'].iloc[-1] < df[f'long_ema_{30}'].iloc[-1]
    is_short_gmma_downward = all(
        (df[f'short_ema_{ema}'].iloc[-1] < df[f'short_ema_{ema}'].iloc[-2]) 
        for ema in short_term_emas
    )
    is_short_gmma_separation = True
    for i in range(0, len(short_term_emas) - 1):
        if df[f'short_ema_{short_term_emas[i]}'].iloc[-1] >= df[f'short_ema_{short_term_emas[i + 1]}'].iloc[-1]:
            is_short_gmma_separation = False
            break

    ### short term STOCH #####################
    is_short_term_stoch_downward = df['stoch_short'].iloc[-1] < df['stoch_short'].iloc[-2]
    ### long term STOCH ######################
    is_long_term_stoch_downward = (df['stoch_long'].iloc[-1] < df['stoch_long'].iloc[-2]
                                   and df['stoch_long'].iloc[-2] < df['stoch_long'].iloc[-3])
    ### RSI #################################
    is_rsi_downward = df['rsi'].iloc[-1] < df['rsi'].iloc[-2]
    is_rsi_below_50 = df['rsi'].iloc[-1] < 50

    is_volume_growing = df['volume_sma'].iloc[-1] > df['volume_sma'].iloc[-2]

    return all([
        is_200ema_downward, 

        is_long_gmma_below_200ema, 
        is_long_gmma_downward,
        is_long_gmma_separation,

        is_short_term_GMMA_below_long_term_GMMA,
        is_short_gmma_downward,
        is_short_gmma_separation,

        is_short_term_stoch_downward,
        is_long_term_stoch_downward,

        is_rsi_downward,
        is_rsi_below_50,

        is_volume_growing
    ])

def is_long_entry(df: pd.DataFrame):
    is_200ema_upward = False
    if df['ema_200'].iloc[-1] > df['ema_200'].iloc[-2]:
        is_200ema_upward = True

    #### long term GMMA ######################
    long_term_emas = [30, 35, 40, 45, 50, 60]
    is_long_gmma_above_200ema = df[f'long_ema_{60}'].iloc[-1] > df['ema_200'].iloc[-1]
    is_long_gmma_upward = all(
        (df[f'long_ema_{ema}'].iloc[-1] > df[f'long_ema_{ema}'].iloc[-2]) 
        for ema in long_term_emas
    )
    is_long_gmma_separation = True
    for i in range(0, len(long_term_emas) - 1):
        if df[f'long_ema_{long_term_emas[i]}'].iloc[-1] <= df[f'long_ema_{long_term_emas[i + 1]}'].iloc[-1]:
            is_long_gmma_separation = False
            break

    #### short term GMMA #######################
    short_term_emas = [3, 5, 8, 10, 12, 15]
    is_short_term_GMMA_above_long_term_GMMA = df[f'short_ema_{15}'].iloc[-1] > df[f'long_ema_{30}'].iloc[-1]
    is_short_gmma_upward = all(
        (df[f'short_ema_{ema}'].iloc[-1] > df[f'short_ema_{ema}'].iloc[-2]) 
        for ema in short_term_emas
    )
    is_short_gmma_separation = True
    for i in range(0, len(short_term_emas) - 1):
        if df[f'short_ema_{short_term_emas[i]}'].iloc[-1] <= df[f'short_ema_{short_term_emas[i + 1]}'].iloc[-1]:
            is_short_gmma_separation = False
            break

    ### short term STOCH #####################
    is_short_term_stoch_upward = df['stoch_short'].iloc[-1] > df['stoch_short'].iloc[-2]
    ### long term STOCH ######################
    is_long_term_stoch_upward = (df['stoch_long'].iloc[-1] > df['stoch_long'].iloc[-2] 
                            and df['stoch_long'].iloc[-2] > df['stoch_long'].iloc[-3]) 
    ### RSI #################################
    is_rsi_upward = df['rsi'].iloc[-1] > df['rsi'].iloc[-2]
    is_rsi_above_50 = df['rsi'].iloc[-1] > 50

    is_volume_growing = df['volume_sma'].iloc[-1] > df['volume_sma'].iloc[-2]

    return all([
        is_200ema_upward, 

        is_long_gmma_above_200ema, 
        is_long_gmma_upward,
        is_long_gmma_separation,

        is_short_term_GMMA_above_long_term_GMMA,
        is_short_gmma_upward,
        is_short_gmma_separation,

        is_short_term_stoch_upward,
        is_long_term_stoch_upward,

        is_rsi_upward,
        is_rsi_above_50,

        is_volume_growing
    ])

def is_long_exit(df: pd.DataFrame):
    ### short term STOCH #####################
    is_short_term_stoch_downward = df['stoch_short'].iloc[-1] < df['stoch_short'].iloc[-2]
    ### long term STOCH ######################
    is_long_term_stoch_downward = df['stoch_long'].iloc[-1] < df['stoch_long'].iloc[-2]
    ### RSI #################################
    is_rsi_downward = df['rsi'].iloc[-1] < df['rsi'].iloc[-2]
    is_rsi_below_50 = df['rsi'].iloc[-1] < 50

    return (
        all([
            is_long_term_stoch_downward,
            is_short_term_stoch_downward,
        ]) or all([
            is_rsi_below_50,
            is_rsi_downward,
        ])
    )

def is_short_exit(df: pd.DataFrame):
    ### short term STOCH #####################
    is_short_term_stoch_upward = df['stoch_short'].iloc[-1] > df['stoch_short'].iloc[-2]
    ### long term STOCH ######################
    is_long_term_stoch_upward = df['stoch_long'].iloc[-1] > df['stoch_long'].iloc[-2]
    ### RSI #################################
    is_rsi_upward = df['rsi'].iloc[-1] > df['rsi'].iloc[-2]
    is_rsi_above_50 = df['rsi'].iloc[-1] > 50

    return (
        all([
            is_long_term_stoch_upward,
            is_short_term_stoch_upward,
        ]) or all([
            is_rsi_above_50,
            is_rsi_upward,
        ])
    )