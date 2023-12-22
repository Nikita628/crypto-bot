CREATE TYPE public.deal_direction AS ENUM ('long', 'short');

CREATE TABLE public.user (
    id serial primary key,
    name character(200) NOT NULL unique,
    email character(200) NOT NULL unique,
    password character(500) NOT NULL
);

insert into public.user (name, email, password)
values ('admin', 'admin@admin.com', 'admin');

CREATE TABLE public.deal (
    id BIGSERIAL primary key,
    symbol character(40) GENERATED ALWAYS AS (base_asset || quote_asset) STORED,
    base_asset character(20) NOT NULL,
    quote_asset character(20) NOT NULL,
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
	strategy character(200) NOT NULL unique
);

CREATE TABLE public.history_data (
    open_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP PRIMARY KEY,
    symbol character(20) NOT NULL,
    open_price real NOT NULL,
    high_price real NOT NULL,
    low_price real NOT NULL,
    close_price real NOT NULL,
    close_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    volume real NOT NULL
);

CREATE TABLE public.asset (
    coin character(20) PRIMARY KEY,
    amount real NOT NULL,
    user_id integer NOT NULL references public.user(id)
);