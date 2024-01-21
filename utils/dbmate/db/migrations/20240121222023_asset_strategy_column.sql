-- migrate:up
ALTER TABLE public.asset
    ADD COLUMN strategy text NOT NULL;

-- migrate:down
ALTER TABLE public.asset
    DROP COLUMN strategy;
