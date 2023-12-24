CREATE TYPE public.trade_direction AS ENUM ('long', 'short');

CREATE TABLE public.user (
    id serial primary key,
    name text NOT NULL unique,
    email text NOT NULL unique,
    password text NOT NULL
);

insert into public.user (name, email, password)
values ('admin', 'admin@admin.com', 'admin');

CREATE TABLE public.trade (
    id BIGSERIAL primary key,
    symbol text GENERATED ALWAYS AS (base_asset || quote_asset) STORED,
    base_asset text NOT NULL,
    quote_asset text NOT NULL,
    entry_price real NOT NULL,
    entry_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    exit_price real,
    exit_date TIMESTAMP WITH TIME ZONE,
    exit_reason text,
    profit_percentage real GENERATED ALWAYS AS 
    (CASE 
        WHEN direction = 'long' THEN (running_price - entry_price) / entry_price * 100
        WHEN direction = 'short' THEN (entry_price - running_price) / entry_price * 100
        ELSE 0
     END) STORED,
    running_price real NOT NULL,
    direction public.trade_direction NOT NULL,
    user_id integer NOT NULL references public.user(id),
	strategy text NOT NULL,
    highest_profit_percentage real NOT NULL default 0
);

CREATE OR REPLACE FUNCTION update_highest_profit_percentage()
RETURNS TRIGGER AS $$
DECLARE
    long_profit real;
    short_profit real;
BEGIN
    IF NEW.direction = 'long' THEN
        long_profit = (NEW.running_price - NEW.entry_price) / NEW.entry_price * 100;
        IF long_profit > NEW.highest_profit_percentage OR OLD.highest_profit_percentage = 0 THEN
            UPDATE public.trade SET highest_profit_percentage = long_profit WHERE id = NEW.id;
        END IF;
    ELSIF NEW.direction = 'short' THEN
        short_profit = (NEW.entry_price - NEW.running_price) / NEW.entry_price * 100;
        IF short_profit > NEW.highest_profit_percentage OR OLD.highest_profit_percentage = 0 THEN
            UPDATE public.trade SET highest_profit_percentage = short_profit WHERE id = NEW.id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_highest_profit_trigger
AFTER UPDATE ON public.trade
FOR EACH ROW
WHEN (NEW.running_price IS DISTINCT FROM OLD.running_price)
EXECUTE FUNCTION update_highest_profit_percentage();

CREATE TABLE public.history_data (
    open_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP PRIMARY KEY,
    symbol text NOT NULL,
    open_price real NOT NULL,
    high_price real NOT NULL,
    low_price real NOT NULL,
    close_price real NOT NULL,
    close_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    volume real NOT NULL
);

CREATE TABLE public.asset (
    coin text PRIMARY KEY,
    amount real NOT NULL,
    user_id integer NOT NULL references public.user(id)
);