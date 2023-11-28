import threading
import csv
import datetime
from enum import Enum

# connect DB and phycopg2
# add 'asset' table

# symbol,entry_price,entry_date,exit_price,exit_date,amount,
# running_profit_percentage,running_price,direction,is_for_trading,is_for_balance

csv_header = ['pair', 'entry_price', 'entry_date', 'exit_price', 'exit_date', 'profit_%', 'running_profit_%', 'running_price', 'direction']
CSV_FILE = 'transactions.csv'
FILE_LOCK = threading.Lock()
EXPIRATION_PERIOD_HOURS = 48

try:
    with FILE_LOCK:
        with open(CSV_FILE, 'x', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=csv_header)
            writer.writeheader()
except FileExistsError:
    pass

############### set transaction id, remove after DB is connected ##############
transaction_id = 0

with FILE_LOCK:
    with open(CSV_FILE, 'r') as file:
        reader = csv.DictReader(file)
        all_pairs = [row for row in reader]

transaction_id = len(all_pairs)

def get_next_transaction_id():
    global transaction_id
    transaction_id += 1
    return transaction_id
#################################################

class TransactionDirection(Enum):
    long = 'long'
    short = 'short'

# convert to Asset
class Transaction:
    def __init__(
            self, 
            id: int,
            pair: str, 
            entry_price: float,
            entry_date: datetime.datetime,
            exit_price: float,
            exit_date: datetime.datetime,
            profit_percentage: float,
            running_profit_percentage: float,
            running_price: float,
            direction: TransactionDirection,
            # amount: float
        ):
        self.id = id
        self.pair = pair
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.exit_price = exit_price
        self.exit_date = exit_date
        self.profit_percentage = profit_percentage
        self.running_profit_percentage = running_profit_percentage
        self.running_price = running_price
        self.direction = direction

# update_asset
def update_transaction(transaction):
    # Read all data from CSV
    with FILE_LOCK:
        with open(CSV_FILE, 'r') as file:
            reader = csv.DictReader(file)
            all_transactions = [row for row in reader]

    # Update the specific pair info
    for transac in all_transactions:
        if transac['id'] == transaction['id']:
            transac.update(transaction)

    # Write the updated data back to CSV
    with FILE_LOCK:
        with open(CSV_FILE, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=all_transactions[0].keys())
            writer.writeheader()
            writer.writerows(all_transactions)


# is_asset(symbol)
def is_symbol_in_open_transaction(symbol: str):
    with FILE_LOCK:
        with open(CSV_FILE, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['pair'] == symbol and row['exit_price'] == '':
                    return True
    return False

# get_assets()
def get_open_transactions():
    with FILE_LOCK:
        with open(CSV_FILE, 'r') as file:
            reader = csv.DictReader(file)
            open_transactions = [row for row in reader if row['exit_price'] == '']
            return open_transactions

# buy_asset
def create_transaction(transaction: Transaction):
    row = ([get_next_transaction_id(), 
            transaction.pair, 
            transaction.entry_price, 
            transaction.entry_date.strftime('%Y-%m-%d %H:%M:%S'), 
            '', '', '', '', '', transaction.direction.value])
    with FILE_LOCK:
        with open(CSV_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)


# asset is expired when price moves within range -/+ 0.5 % 
# more then 2 days in a row
def is_expired(transaction: Transaction) -> bool:
    # implement
    # if now - entry > EXPIRATION_PERIOD
    # return true
    return False

# sell_asset(asset)

# get_balance()

def is_trailing_stop_hit() -> bool:
    return False