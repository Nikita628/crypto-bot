CREATE TYPE public.deal_direction AS ENUM ('long', 'short');

CREATE TABLE public.user (
    id serial primary key,
    name text NOT NULL unique,
    email text NOT NULL unique,
    password text NOT NULL
);

insert into public.user (name, email, password)
values ('admin', 'admin@admin.com', 'admin');

CREATE TABLE public.deal (
    id BIGSERIAL primary key,
    symbol text GENERATED ALWAYS AS (base_asset || quote_asset) STORED,
    base_asset text NOT NULL,
    quote_asset text NOT NULL,
    entry_price real NOT NULL,
    entry_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    exit_price real,
    exit_date TIMESTAMP WITH TIME ZONE,
    profit_percentage real GENERATED ALWAYS AS 
    (CASE 
        WHEN direction = 'long' THEN (running_price - entry_price) / entry_price * 100
        WHEN direction = 'short' THEN (entry_price - running_price) / entry_price * 100
        ELSE 0
     END) STORED,
    running_price real NOT NULL,
    direction public.deal_direction NOT NULL,
    user_id integer NOT NULL references public.user(id),
	strategy text NOT NULL
);

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