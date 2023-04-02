
CREATE TABLE public.answers (
    prompt text,
    question text,
    id text NOT NULL,
    prompt_id text,
    date text,
    username text,
    status text
);

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT answers_pkey PRIMARY KEY (id);

