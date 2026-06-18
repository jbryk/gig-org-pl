/* ============================================================
   GIG Admin Panel — wspólny JS
   ------------------------------------------------------------
   KONFIGURACJA — uzupełnij po założeniu projektu Supabase:
   https://supabase.com → New project → Settings → API
   ============================================================ */

const SUPABASE_URL  = 'https://zlepwzeyjwpmhyxfnime.supabase.co';
const SUPABASE_ANON = 'sb_publishable_1KPF4mdln3C-cZHMIqAOFw_ZM8Go2Ji';

const { createClient } = supabase;
const db = createClient(SUPABASE_URL, SUPABASE_ANON);

/* ── Auth ── */
async function getSession() {
  const { data } = await db.auth.getSession();
  return data.session;
}
async function requireAuth() {
  const session = await getSession();
  if (!session) { window.location.href = 'index.html'; return null; }
  return session;
}
async function logout() {
  await db.auth.signOut();
  window.location.href = 'index.html';
}

/* ── Toasty ── */
let toastContainer;
function initToasts() {
  toastContainer = document.createElement('div');
  toastContainer.className = 'toast-container';
  document.body.appendChild(toastContainer);
}
function toast(msg, type = 'default', duration = 3500) {
  if (!toastContainer) initToasts();
  const icons = { success: '✓', error: '✕', default: 'ℹ' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${msg}</span>`;
  toastContainer.appendChild(el);
  setTimeout(() => el.remove(), duration);
}

/* ── Sidebar: aktywny link ── */
function highlightNav() {
  const page = location.pathname.split('/').pop() || 'index.html';
  const hash = location.hash;
  document.querySelectorAll('.sidebar-nav a').forEach(a => {
    a.classList.remove('active');
    const full = a.getAttribute('href') || '';
    const base = full.split('#')[0];
    const linkHash = full.includes('#') ? full.slice(full.indexOf('#')) : '';
    const samePage = base === page || base.endsWith('/' + page);
    if (!samePage) return;
    if (linkHash) { if (linkHash === hash) a.classList.add('active'); }
    else if (!hash) { a.classList.add('active'); }
  });
}

/* ── Sidebar: badge z liczbą NOWYCH ── */
async function loadSidebarBadges() {
  const map = [
    { table: 'submissions_newsletter', id: 'navBadgeNewsletter' },
    { table: 'submissions_kontakt',    id: 'navBadgeKontakt' },
  ];
  for (const m of map) {
    const el = document.getElementById(m.id);
    if (!el) continue;
    try {
      const { count } = await db.from(m.table)
        .select('id', { count: 'exact', head: true })
        .eq('status', 'new');
      if (count && count > 0) { el.textContent = count; el.style.display = ''; }
      else { el.style.display = 'none'; }
    } catch (_) { el.style.display = 'none'; }
  }
}

/* ── Dane użytkownika w sidebarze ── */
async function fillUserInfo() {
  const session = await getSession();
  if (!session) return;
  const email = session.user.email || '';
  const el = document.getElementById('userAvatar');
  const ne = document.getElementById('userName');
  if (el) el.textContent = email.charAt(0).toUpperCase();
  if (ne) ne.textContent = email;
}

/* ── Taby ── */
function initTabs(containerSelector) {
  const container = document.querySelector(containerSelector || '.tabs-root');
  if (!container) return;
  const btns = container.querySelectorAll('.tab-btn');
  const panes = container.querySelectorAll('.tab-pane');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      btns.forEach(b => b.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const pane = container.querySelector(`.tab-pane[data-tab="${target}"]`);
      if (pane) pane.classList.add('active');
    });
  });
  if (btns.length > 0 && !container.querySelector('.tab-btn.active')) btns[0].click();
}

/* ── Modale ── */
function openModal(id) { const m = document.getElementById(id); if (m) m.classList.add('open'); }
function closeModal(id) { const m = document.getElementById(id); if (m) m.classList.remove('open'); }
function initModals() {
  document.querySelectorAll('[data-modal-open]').forEach(btn =>
    btn.addEventListener('click', () => openModal(btn.dataset.modalOpen)));
  document.querySelectorAll('[data-modal-close]').forEach(btn =>
    btn.addEventListener('click', () => closeModal(btn.dataset.modalClose)));
  document.querySelectorAll('.modal-overlay').forEach(overlay =>
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.classList.remove('open'); }));
}

/* ── Format daty ── */
function fmtDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric' })
    + ' ' + d.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });
}

/* ── Eksport CSV ── */
function exportCSV(rows, columns, filename) {
  const header = columns.map(c => c.label).join(';');
  const body = rows.map(row =>
    columns.map(c => `"${(row[c.key] ?? '').toString().replace(/"/g, '""')}"`).join(';')
  ).join('\n');
  const blob = new Blob(['﻿' + header + '\n' + body], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

/* ── Escape ── */
function esc(s) {
  return (s ?? '').toString()
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ── Init ── */
document.addEventListener('DOMContentLoaded', () => {
  initToasts();
  initModals();
  highlightNav();
  fillUserInfo();
  loadSidebarBadges();
  window.addEventListener('hashchange', highlightNav);
  document.querySelectorAll('[data-action="logout"]').forEach(btn => btn.addEventListener('click', logout));
});
