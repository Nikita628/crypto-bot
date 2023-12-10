import threading
import csv
import datetime
from enum import Enum

csv_header = [
    'id', 'pair', 'entry_price', 'entry_date', 'exit_price', 
    'exit_date', 'profit_%', 'running_profit_%', 
    'running_price', 'direction', 'highest_profit_%'
]
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
    transaction_id = transaction_id + 1
    return transaction_id
#################################################

class TransactionDirection(Enum):
    long = 'long'
    short = 'short'

# convert to Asset
class Transaction:
    def __init__(
            self, 
            pair: str, 
            entry_price: float,
            entry_date: datetime.datetime,
            exit_price: float,
            exit_date: datetime.datetime,
            profit_percentage: float,
            running_profit_percentage: float,
            running_price: float,
            direction: TransactionDirection,
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

def update_transaction(transaction):
    with FILE_LOCK:
        with open(CSV_FILE, 'r') as file:
            reader = csv.DictReader(file)
            all_transactions = [row for row in reader]

    for transac in all_transactions:
        if transac['id'] == transaction['id']:
            transac.update(transaction)

    with FILE_LOCK:
        with open(CSV_FILE, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=all_transactions[0].keys())
            writer.writeheader()
            writer.writerows(all_transactions)


def is_symbol_in_open_transaction(symbol: str):
    with FILE_LOCK:
        with open(CSV_FILE, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['pair'] == symbol and row['exit_price'] == '':
                    return True
    return False


def get_open_transactions():
    with FILE_LOCK:
        with open(CSV_FILE, 'r') as file:
            reader = csv.DictReader(file)
            open_transactions = [row for row in reader if row['exit_price'] == '']
            return open_transactions


def create_transaction(transaction: Transaction):
    row = ([
        get_next_transaction_id(), 
        transaction.pair, 
        transaction.entry_price, 
        transaction.entry_date.strftime('%Y-%m-%d %H:%M:%S'), 
        '', 
        '', 
        '', 
        '', 
        '', 
        transaction.direction.value,
        transaction.entry_price,
    ])
    with FILE_LOCK:
        with open(CSV_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)

