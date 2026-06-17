# Projekt: gig.org.pl — migracja WordPress → statyka + panel

## Cel
Migracja strony **Geodezyjnej Izby Gospodarczej** (gig.org.pl) z WordPressa na **statykę
hostowaną na Vercel**, z panelem administracyjnym `/admin/` (Supabase + Resend) do obsługi
newslettera, formularza kontaktowego i artykułów (aktualności/biuletyn).

## Architektura
- **Frontend**: statyczny mirror WP (Elementor/BeTheme), katalog deployowany: `strona/`.
- **Backend**: Supabase (PostgreSQL + Auth + Edge Functions), maile przez Resend.
- **Panel**: `/admin/` — login, pulpit, formularze (newsletter+kontakt), artykuły (CRUD, edytor Quill).
- Formularze CF7 przechwytywane przez `_assets/js/forms_integration.js` → Supabase (fallback `mailto:`).

## Jak powstał mirror (skrypty w `skrypty/`, POZA deployem)
1. `crawl.py` — pobrał strony + zasoby, zlokalizował URL-e (root-relative), zachował strukturę.
2. `clean.py` — usunął cruft WP (emoji, oEmbed, REST, generator), ustawił canonical, wstrzyknął `forms_integration.js`.
3. `gen_sitemap.py` — wygenerował `strona/sitemap.xml` (pomija /admin/ i strony demo).
Skrypty są **idempotentne** — można powtórzyć (np. po aktualizacji treści w WP przed ostatecznym odcięciem).

## Dane GIG (z mirrora)
- Geodezyjna Izba Gospodarcza, ul. Czackiego 3/5, 00-043 Warszawa
- tel. 22 827 38 43 · biuro@gig.org.pl · NIP 525-20-34-024 · REGON 010753536
- Menu: O nas / Baza wiedzy (Aktualności, Artykuły, Biuletyn) / Szkolenia / Dołącz do nas / Kontakt

## ⚠️ Placeholdery do uzupełnienia (po założeniu Supabase)
- `strona/admin/_admin.js` → `SUPABASE_URL`, `SUPABASE_ANON`
- `strona/_assets/js/forms_integration.js` → `SUPABASE_URL`, `SUPABASE_ANON` (te same)
- Sekrety Resend w Supabase (Edge Functions): `RESEND_API_KEY`, `FROM_EMAIL`, `SITE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- Konto admina: Supabase → Authentication → Users → Add user (np. biuro@gig.org.pl)

## Żelazne zasady
- Front używa wyłącznie klucza `sb_publishable_` (anon). `service_role`/`re_...` tylko w sekretach Supabase.
- Katalog `skrypty/` i `backend/` NIE są deployowane (Root Directory na Vercel = `strona/`).
- Canonical i domena: **gig.org.pl bez www** (www → 301 na apex w `vercel.json`).

## Znane do dokończenia
- **Duże biuletyny PDF (>25 MB)** — pominięte przy mirrorze, linki zostały absolutne (`gig.org.pl/biuletyn/...`).
  Po migracji domeny trzeba je dograć ręcznie do `strona/biuletyn/` albo wrzucić do Supabase Storage.
- **Publiczne renderowanie artykułów z panelu** — panel zapisuje do `articles`; podpięcie wyświetlania
  na stronach Aktualności/Artykuły (client-side fetch z Supabase) to następny krok.
- Mirror to snapshot — dynamiczne listy WP są „zamrożone".
