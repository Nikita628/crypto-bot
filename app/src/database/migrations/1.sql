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
    symbol character(20) NOT NULL,
    entry_price real NOT NULL,
    entry_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    exit_price real,
    exit_date TIMESTAMP WITH TIME ZONE,
    running_profit_percentage real NOT NULL default 0,
    running_price real NOT NULL,
    direction public.deal_direction NOT NULL,
    user_id integer NOT NULL references public.user(id)
);

CREATE TABLE public.history_data (
    date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE public.asset (
    coin character(20) PRIMARY KEY,
    amount real NOT NULL,
    user_id integer NOT NULL references public.user(id)
);