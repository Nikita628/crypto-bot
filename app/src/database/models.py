from peewee import *
import os

db = PostgresqlDatabase(
    database=os.environ.get('POSTGRES_DB'), 
    user=os.environ.get('POSTGRES_USER'), 
    password=os.environ.get('POSTGRES_PASSWORD'), 
    host=os.environ.get('POSTGRES_HOST')
)

class Base(Model):
    class Meta:
        database = db


class User(Base):
    id = AutoField(column_name='id', primary_key=True)
    name = TextField(column_name='name', null=True)
    email = TextField(column_name='email', null=False)
    password = TextField(column_name='password', null=False)
    
    class Meta:
        table_name = 'user'


class Asset(Base):
    id = AutoField(column_name='id', primary_key=True)
    coin = TextField(column_name='coin', null=False)
    amount = FloatField(column_name='amount', null=False)
    strategy = TextField(column_name='strategy', null=False)
    user_id = ForeignKeyField(User, related_name='id')

    class Meta:
        table_name = 'asset'


class Trade(Base):
    id = AutoField(column_name='id', primary_key=True)
    symbol = TextField(column_name='symbol', null=True)
    base_asset = TextField(column_name='base_asset', null=False)
    base_asset_amount = FloatField(column_name='base_asset_amount', null=False)
    quote_asset = TextField(column_name='quote_asset', null=False)
    quote_asset_amount = FloatField(column_name='quote_asset_amount', null=True)
    entry_price = FloatField(column_name='entry_price', null=False)
    entry_date = DateTimeField(column_name='entry_date', null=False)
    exit_price = FloatField(column_name='exit_price', null=True)
    exit_date = DateTimeField(column_name='exit_date', null=True)
    exit_reason = TextField(column_name='exit_reason', null=True)
    profit_percentage = FloatField(column_name='profit_percentage', null=True)
    highest_profit_percentage = FloatField(column_name='highest_profit_percentage', null=False)
    running_price = FloatField(column_name='running_price', null=False)
    direction = TextField(column_name='direction', null=False)
    user_id = ForeignKeyField(User, related_name='id', null=False)
    strategy = TextField(column_name='strategy', null=False)
    atr_percentage = FloatField(column_name='atr_percentage', null=False)
    class Meta:
        table_name = 'trade'


class Hold(Base):
    id = AutoField(column_name='id', primary_key=True)
    symbol = TextField(column_name='symbol', null=False)
    strategy = TextField(column_name='strategy', null=False)
    start_time = DateTimeField(column_name='start_time', null=False)
    end_time = DateTimeField(column_name='end_time', null=False)
    user_id = ForeignKeyField(User, related_name='id', null=False)

    class Meta:
        table_name = 'hold'


class HistoryData(Base):
    symbol = TextField(column_name='symbol', primary_key=True)
    open_time = DateTimeField(column_name='open_time', null=False)
    open_price = FloatField(column_name='open_price', null=False)
    high_price = FloatField(column_name='high_price', null=False)
    low_price = FloatField(column_name='low_price', null=False)
    close_price = FloatField(column_name='close_price', null=False)
    close_time = DateTimeField(column_name='close_time', null=False)
    volume = FloatField(column_name='volume', null=False)
    
    class Meta:
        table_name = 'history_data'


