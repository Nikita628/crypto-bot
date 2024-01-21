-- migrate:up
CREATE TABLE public.hold (
                              id BIGSERIAL primary key,
                              symbol text NOT NULL,
                              strategy text NOT NULL,
                              start_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                              end_time TIMESTAMP WITH TIME ZONE NOT NULL,
                              user_id integer NOT NULL references public.user(id)
);

-- migrate:down
DROP TABLE IF EXISTS public.hold;
