import pandas as pd
from technical_indicators import (
    add_200ema,
    add_gmma,
    add_rsi,
    add_stoch_osc,
    add_volume_sma,
    add_mfi,
    add_pvt,
)
from binance import BinanceInterval, get_all_usdt_symbols, get_kline
from transaction import (
    Transaction,
    TransactionDirection,
    get_open_transactions, 
    create_transaction,
    is_symbol_in_open_transaction,
    update_transaction,
    exit_all
)
import datetime
import time

LOOCKBACK = 501 # need 501 for proper calculation of EMA according to Binance
INTERVAL = BinanceInterval.day
SLEEP_ENTRY = 120
SLEEP_EXIT = 30

def search_entry():
    usdt_symbols = sorted(get_all_usdt_symbols())
    checked_symbols = 0

    while True:
        print(f'searching entry...')
        checked_symbols = 0
        for symbol in usdt_symbols:
            checked_symbols += 1
            try:
                if checked_symbols % 10 == 0:
                    print(f'searched {checked_symbols} symbols...')

                if is_symbol_in_open_transaction(symbol):
                    continue

                df = get_kline(symbol, INTERVAL, LOOCKBACK)

                if len(df) < LOOCKBACK:
                    continue
        
                add_gmma(df)
                add_200ema(df)
                add_rsi(df)
                add_volume_sma(df)
                add_stoch_osc(df, 5, 3, 2, 'short')
                add_stoch_osc(df, 20, 3, 8, 'long')
                add_pvt(df)
                add_mfi(df)
                is_long = is_long_entry(df)
                is_short = is_short_entry(df)

                if is_long or is_short:
                    print(f'going {TransactionDirection.long.value if is_long else TransactionDirection.short.value} - {symbol}')

                    create_transaction(Transaction(
                        pair=symbol,
                        entry_price=df['close'].iloc[-1],
                        entry_date=datetime.datetime.utcnow(),
                        direction=TransactionDirection.long if is_long else TransactionDirection.short,
                        exit_price=0,
                        exit_date='',
                        profit_percentage=0,
                        running_profit_percentage=0,
                        running_price=0,
                    ))
            except Exception as e:
                print(f"search_entry: Failed to process data for {symbol}: {e}")
                
            time.sleep(2)
            
        time.sleep(SLEEP_ENTRY)

def search_exit():
    while True:
        print(f'searching exit...')

        open_transactions = get_open_transactions()

        for transaction in open_transactions:
            try:
                df = get_kline(transaction['pair'], INTERVAL, LOOCKBACK)
                add_rsi(df)
                add_stoch_osc(df, 5, 3, 2, 'short')
                add_stoch_osc(df, 20, 3, 8, 'long')
                trade_direction = transaction['direction']

                if trade_direction == TransactionDirection.long.value and is_long_exit(df):
                    print(f'exiting long - {transaction["pair"]}')
                    transaction['exit_price'] = df['close'].iloc[-1]
                    transaction['exit_date'] = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    profit = df['close'].iloc[-1] - float(transaction['entry_price'])
                    transaction['profit_%'] = profit * 100 / float(transaction['entry_price'])
                    transaction['highest_profit_%'] = (
                        transaction['profit_%'] 
                        if float(transaction['profit_%'] or 0) > float(transaction['highest_profit_%'] or 0) 
                        else transaction['highest_profit_%'] or transaction['profit_%']
                    )
                elif trade_direction == TransactionDirection.short.value and is_short_exit(df):
                    print(f'exiting short - {transaction["pair"]}')
                    transaction['exit_price'] = df['close'].iloc[-1]
                    transaction['exit_date'] = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    profit = float(transaction['entry_price']) - df['close'].iloc[-1]
                    transaction['profit_%'] = profit * 100 / float(transaction['entry_price'])
                    transaction['highest_profit_%'] = (
                        transaction['profit_%'] 
                        if float(transaction['profit_%'] or 0) > float(transaction['highest_profit_%'] or 0) 
                        else transaction['highest_profit_%'] or transaction['profit_%']
                    )
                else:
                    profit = (
                        df['close'].iloc[-1] - float(transaction['entry_price']) 
                        if trade_direction == TransactionDirection.long.value
                        else float(transaction['entry_price']) - df['close'].iloc[-1]
                    )
                    transaction['running_profit_%'] = profit * 100 / float(transaction['entry_price'])
                    transaction['running_price'] = df['close'].iloc[-1]
                    transaction['highest_profit_%'] = (
                        transaction['running_profit_%'] 
                        if float(transaction['running_profit_%'] or 0) > float(transaction['highest_profit_%'] or 0) 
                        else transaction['highest_profit_%'] or transaction['running_profit_%'] 
                    )

                # trailing stop
                highest_profit_percentage = float(transaction['highest_profit_%'])
                running_profit_percentage = float(transaction['running_profit_%'])
                trailing_stop_percentage = 1 if highest_profit_percentage > 2 else 6
                max_allowed_loss_percentage = -4

                if (running_profit_percentage < max_allowed_loss_percentage 
                    or abs(highest_profit_percentage - running_profit_percentage) > trailing_stop_percentage):
                    print(f'exiting by trailing stop - {transaction["pair"]}')
                    profit = (
                        df['close'].iloc[-1] - float(transaction['entry_price']) 
                        if trade_direction == TransactionDirection.long.value
                        else float(transaction['entry_price']) - df['close'].iloc[-1]
                    )
                    transaction['running_profit_%'] = profit * 100 / float(transaction['entry_price'])
                    transaction['running_price'] = df['close'].iloc[-1]
                    transaction['exit_price'] = df['close'].iloc[-1]
                    transaction['exit_date'] = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    transaction['profit_%'] = profit * 100 / float(transaction['entry_price'])

                update_transaction(transaction)
                
            except Exception as e:
                print(f"search_exit: Failed to process data for {transaction['pair']}: {e}")

        time.sleep(SLEEP_EXIT)

def is_short_entry(df: pd.DataFrame):
    ### 200 EMA #############################
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
    is_short_term_stoch_oversold = df['stoch_short'].iloc[-1] < 20
    
    ### long term STOCH ######################
    is_long_term_stoch_downward = (df['stoch_long'].iloc[-1] < df['stoch_long'].iloc[-2]
                                   and df['stoch_long'].iloc[-2] < df['stoch_long'].iloc[-3])
    is_long_term_stoch_oversold = df['stoch_long'].iloc[-1] < 20

    ### RSI #################################
    is_rsi_downward = df['rsi'].iloc[-1] < df['rsi'].iloc[-2]
    is_rsi_below_50 = df['rsi'].iloc[-1] < 50
    is_rsi_oversold = df['rsi'].iloc[-1] < 20

    ### Volume ##############################
    is_volume_growing = df['volume_sma'].iloc[-1] > df['volume_sma'].iloc[-2]

    ### PVT #################################
    is_pvt_downward = (df['pvt'].iloc[-1] < df['pvt'].iloc[-2] 
                    and df['pvt'].iloc[-2] < df['pvt'].iloc[-3])
    
    ### MFI #################################
    is_mfi_downward = df['mfi'].iloc[-1] < df['mfi'].iloc[-2]
    is_mfi_below_highest = df['mfi'].iloc[-1] < 60
    is_mfi_oversold = df['mfi'].iloc[-1] < 20

    return all([
        is_200ema_downward, 

        is_long_gmma_below_200ema, 
        is_long_gmma_downward,
        is_long_gmma_separation,

        is_short_term_GMMA_below_long_term_GMMA,
        is_short_gmma_downward,
        is_short_gmma_separation,

        is_short_term_stoch_downward,
        (not is_short_term_stoch_oversold),

        is_long_term_stoch_downward,
        # (not is_long_term_stoch_oversold),

        # is_rsi_downward,
        # is_rsi_below_50,
        # (not is_rsi_oversold),

        # is_volume_growing,

        is_pvt_downward,

        is_mfi_downward,
        is_mfi_below_highest,
        (not is_mfi_oversold),
    ])

def is_long_entry(df: pd.DataFrame):
    ### 200 EMA ############################
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
    is_short_term_stoch_overbought = df['stoch_short'].iloc[-1] > 85

    ### long term STOCH ######################
    is_long_term_stoch_upward = (df['stoch_long'].iloc[-1] > df['stoch_long'].iloc[-2] 
                            and df['stoch_long'].iloc[-2] > df['stoch_long'].iloc[-3]) 
    is_long_term_stoch_overbought = df['stoch_long'].iloc[-1] > 85

    ### RSI #################################
    is_rsi_upward = df['rsi'].iloc[-1] > df['rsi'].iloc[-2]
    is_rsi_above_50 = df['rsi'].iloc[-1] > 50
    is_rsi_overbought = df['rsi'].iloc[-1] > 85

    ### Volume ##############################
    is_volume_growing = df['volume_sma'].iloc[-1] > df['volume_sma'].iloc[-2]

    ### PVT #################################
    is_pvt_upward = (df['pvt'].iloc[-1] > df['pvt'].iloc[-2] 
                    and df['pvt'].iloc[-2] > df['pvt'].iloc[-3])
    
    ### MFI #################################
    is_mfi_upward = df['mfi'].iloc[-1] > df['mfi'].iloc[-2]
    is_mfi_above_lowest = df['mfi'].iloc[-1] > 40
    is_mfi_overbought = df['mfi'].iloc[-1] > 85

    return all([
        is_200ema_upward, 

        is_long_gmma_above_200ema, 
        is_long_gmma_upward,
        is_long_gmma_separation,

        is_short_term_GMMA_above_long_term_GMMA,
        is_short_gmma_upward,
        is_short_gmma_separation,

        is_short_term_stoch_upward,
        (not is_short_term_stoch_overbought),

        is_long_term_stoch_upward,
        # (not is_long_term_stoch_overbought),

        # is_rsi_upward,
        # is_rsi_above_50,
        # (not is_rsi_overbought),

        # is_volume_growing

        is_pvt_upward,

        is_mfi_upward,
        is_mfi_above_lowest,
        (not is_mfi_overbought),
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


#average_profit_percentage = (
        #     sum([float(transaction["running_profit_%"] or 0) for transaction in open_transactions]) / len(open_transactions)
        #     if len(open_transactions) > 0
        #     else 0
        # )
        # current_date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # with open('log.txt', 'a') as file:
        #     if (average_profit_percentage > 1):
        #         print(f'{current_date}: sell all ({len(open_transactions)}), take profit: {average_profit_percentage}', file=file)
        #         exit_all()
        #     else:
        #         print(f'{current_date}: average profit: {average_profit_percentage}', file=file)