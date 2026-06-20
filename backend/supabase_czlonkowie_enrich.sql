-- =====================================================================
-- GIG — rozszerzenie tabeli `czlonkowie` o dane wzbogacone
-- (NIP/REGON/KRS z GUS, www/FB/LinkedIn z wyszukiwarki, opis, geo-pinezki)
-- Uruchom RAZ w Supabase → SQL Editor. Idempotentne (IF NOT EXISTS).
-- Dane wgrywane są osobnym plikiem UPDATE (generowanym przez skrypt).
-- =====================================================================
alter table public.czlonkowie add column if not exists nip       text;
alter table public.czlonkowie add column if not exists regon     text;
alter table public.czlonkowie add column if not exists krs       text;
alter table public.czlonkowie add column if not exists facebook  text;
alter table public.czlonkowie add column if not exists linkedin  text;
alter table public.czlonkowie add column if not exists lat       double precision;
alter table public.czlonkowie add column if not exists lng       double precision;
-- (website i description już istnieją z pierwotnego schematu)
