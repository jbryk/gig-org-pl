-- ============================================================
-- Geodezyjna Izba Gospodarcza (gig.org.pl) — Supabase setup
-- Uruchom w: Supabase → SQL Editor → New query → Run
-- ============================================================

-- ─── Newsletter ───
CREATE TABLE IF NOT EXISTS submissions_newsletter (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email       TEXT NOT NULL UNIQUE,
  status      TEXT DEFAULT 'new' CHECK (status IN ('new','read','unsubscribed')),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Formularz kontaktowy ───
CREATE TABLE IF NOT EXISTS submissions_kontakt (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name        TEXT,
  email       TEXT NOT NULL,
  subject     TEXT,
  message     TEXT,
  status      TEXT DEFAULT 'new' CHECK (status IN ('new','read','replied')),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Artykuły / Aktualności / Biuletyn (zarządzane z panelu) ───
CREATE TABLE IF NOT EXISTS articles (
  id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title        TEXT NOT NULL,
  slug         TEXT UNIQUE,
  content      TEXT,
  excerpt      TEXT,
  category     TEXT DEFAULT 'aktualnosci',
  status       TEXT DEFAULT 'draft' CHECK (status IN ('draft','published','archived')),
  published_at TIMESTAMPTZ,
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  updated_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_articles_status   ON articles (status, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_kontakt_created   ON submissions_kontakt (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_newsletter_created ON submissions_newsletter (created_at DESC);

-- ─── RLS ───
ALTER TABLE submissions_newsletter ENABLE ROW LEVEL SECURITY;
ALTER TABLE submissions_kontakt    ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles               ENABLE ROW LEVEL SECURITY;

-- Newsletter: publiczny INSERT, odczyt/edycja tylko admin
DROP POLICY IF EXISTS "nl public insert" ON submissions_newsletter;
CREATE POLICY "nl public insert" ON submissions_newsletter FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS "nl admin all" ON submissions_newsletter;
CREATE POLICY "nl admin all" ON submissions_newsletter FOR ALL USING (auth.role() = 'authenticated');

-- Kontakt: publiczny INSERT, odczyt/edycja tylko admin
DROP POLICY IF EXISTS "kt public insert" ON submissions_kontakt;
CREATE POLICY "kt public insert" ON submissions_kontakt FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS "kt admin all" ON submissions_kontakt;
CREATE POLICY "kt admin all" ON submissions_kontakt FOR ALL USING (auth.role() = 'authenticated');

-- Artykuły: admin pełny dostęp; publiczny odczyt tylko opublikowanych
DROP POLICY IF EXISTS "art admin all" ON articles;
CREATE POLICY "art admin all" ON articles FOR ALL USING (auth.role() = 'authenticated');
DROP POLICY IF EXISTS "art public read published" ON articles;
CREATE POLICY "art public read published" ON articles FOR SELECT USING (status = 'published');

-- ─── Konto administratora ───
-- Authentication → Users → "Add user" → e-mail (np. biuro@gig.org.pl) + hasło.
-- Wyłącz publiczną rejestrację: Authentication → Sign In / Providers → wyłącz "Allow new users to sign up".
