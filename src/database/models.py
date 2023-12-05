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
    name = FixedCharField(column_name='name', null=True)
    email = FixedCharField(column_name='email', null=False)
    password = FixedCharField(column_name='password', null=False)
    
    class Meta:
        table_name = 'user'


class Asset(Base):
    coin = FixedCharField(column_name='coin', primary_key=True)
    amount = FloatField(column_name='amount', null=False)
    user_id = ForeignKeyField(User, related_name='id')

    class Meta:
        table_name = 'asset'


class Deal(Base):
    id = AutoField(column_name='id', primary_key=True)
    symbol = FixedCharField(column_name='symbol', null=False)
    entry_price = FloatField(column_name='entry_price', null=False)
    entry_date = DateTimeField(column_name='entry_date', null=False)
    exit_price = FloatField(column_name='exit_price', null=True)
    exit_date = DateTimeField(column_name='exit_date', null=True)
    running_profit_percentage = FloatField(column_name='running_profit_percentage', null=False)
    running_price = FloatField(column_name='running_price', null=False)
    direction = FixedCharField(column_name='direction', null=False)
    user_id = ForeignKeyField(User, related_name='id', null=False)

    class Meta:
        table_name = 'deal'


class SuspendedSymbol(Base):
    suspention_start_date = DateTimeField(column_name='suspention_start_date', primary_key=True)
    symbol = FixedCharField(column_name='symbol', null=False)

    class Meta:
        table_name = 'suspended_symbol'


class HistoryData(Base):
    date = DateTimeField(column_name='date', primary_key=True)
    
    class Meta:
        table_name = 'history_data'


