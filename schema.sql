--
-- PostgreSQL database dump
--

-- Dumped from database version 14.5
-- Dumped by pg_dump version 14.5 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: answer; Type: TABLE; Schema: public; Owner: james
--

CREATE TABLE public.answer (
    prompt text,
    question text,
    id text NOT NULL,
    prompt_id text,
    date text,
    username text,
    status text
);


ALTER TABLE public.answer OWNER TO james;

--
-- Name: answers; Type: TABLE; Schema: public; Owner: james
--

CREATE TABLE public.answers (
    prompt text,
    question text,
    id text NOT NULL,
    prompt_id text,
    date text,
    username text,
    status text
);


ALTER TABLE public.answers OWNER TO james;

--
-- Name: answer answer_pkey; Type: CONSTRAINT; Schema: public; Owner: james
--

ALTER TABLE ONLY public.answer
    ADD CONSTRAINT answer_pkey PRIMARY KEY (id);


--
-- Name: answers answers_pkey; Type: CONSTRAINT; Schema: public; Owner: james
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT answers_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

