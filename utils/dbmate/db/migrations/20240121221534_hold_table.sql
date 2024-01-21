-- migrate:up
CREATE TABLE public.hold (
                              id BIGSERIAL primary key,
                              symbol text NOT NULL,
                              strategy text NOT NULL,
                              start_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                              end_time TIMESTAMP WITH TIME ZONE NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS public.hold;
