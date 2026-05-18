/* spark app — navigation & interactions (rail + tabs) */
(function(){
  const screens = ['busca','resultados','detalhes','perfil','admin'];

  const titleMap = {
    busca:      { icon: 'search',       title: 'busca',        crumb: 'spark / busca' },
    resultados: { icon: 'list-filter',  title: 'resultados',   crumb: 'spark / busca / resultados' },
    detalhes:   { icon: 'file-text',    title: 'produção',     crumb: 'spark / busca / produção' },
    perfil:     { icon: 'user-round',   title: 'pesquisador',  crumb: 'spark / pesquisador' },
    admin:      { icon: 'settings-2',   title: 'painel admin', crumb: 'spark / admin' },
  };

  function setTopbar(id) {
    const conf = titleMap[id];
    if (!conf) return;
    const titleEl = document.getElementById('topbar-title');
    const crumbEl = document.getElementById('topbar-crumbs');
    if (titleEl) {
      titleEl.innerHTML = `<i data-lucide="${conf.icon}" class="i-md"></i>${conf.title}`;
    }
    if (crumbEl) crumbEl.textContent = conf.crumb;

    const ts = document.getElementById('topbar-search');
    if (ts) ts.style.visibility = (id === 'busca') ? 'hidden' : 'visible';

    if (window.lucide) lucide.createIcons();
  }

  function showScreen(id) {
    screens.forEach(s => {
      const el = document.getElementById('screen-' + s);
      if (el) el.classList.remove('active');
    });
    document.querySelectorAll('.rail-item').forEach(b => b.classList.remove('active'));
    const target = document.getElementById('screen-' + id);
    if (target) target.classList.add('active');
    const btn = document.querySelector(`.rail-item[data-screen="${id}"]`);
    if (btn) btn.classList.add('active');
    setTopbar(id);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }

  // ---- Rail nav ----
  document.querySelectorAll('.rail-item[data-screen]').forEach(btn => {
    btn.addEventListener('click', () => showScreen(btn.dataset.screen));
  });

  // ---- Generic data-screen (back links) ----
  document.querySelectorAll('[data-screen]').forEach(el => {
    if (el.classList.contains('rail-item')) return;
    el.addEventListener('click', e => {
      if (el.classList.contains('admin-tab')) return;
      if (el.classList.contains('profile-tab')) return;
      showScreen(el.dataset.screen);
    });
  });

  // ---- data-go (cards → telas) ----
  document.querySelectorAll('[data-go]').forEach(el => {
    el.addEventListener('click', () => showScreen(el.dataset.go));
  });

  // ---- Home search interactions ----
  const homeBtn = document.getElementById('home-search-btn');
  const homeInput = document.getElementById('home-input');
  if (homeBtn) homeBtn.addEventListener('click', () => showScreen('resultados'));
  if (homeInput) homeInput.addEventListener('keydown', e => { if (e.key === 'Enter') showScreen('resultados'); });

  // ---- Topbar input ----
  const topInput = document.getElementById('topbar-input');
  if (topInput) topInput.addEventListener('keydown', e => { if (e.key === 'Enter') showScreen('resultados'); });

  // ---- ⌘K shortcut ----
  document.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (topInput && topInput.offsetParent) topInput.focus();
      else if (homeInput) homeInput.focus();
    }
    if (e.key === 'Escape' && document.activeElement && document.activeElement.tagName === 'INPUT') {
      document.activeElement.blur();
    }
  });

  // ---- Mode toggle groups ----
  document.querySelectorAll('.mode-toggle').forEach(group => {
    group.querySelectorAll('.mode-btn').forEach(b => {
      b.addEventListener('click', () => {
        group.querySelectorAll('.mode-btn').forEach(x => x.classList.remove('active'));
        b.classList.add('active');
      });
    });
  });

  // ---- Admin top tabs ----
  document.querySelectorAll('.admin-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.admin-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.admin-section').forEach(s => s.classList.remove('active'));
      const sec = document.getElementById(btn.dataset.sec);
      if (sec) sec.classList.add('active');
    });
  });

  // ---- Profile tabs ----
  document.querySelectorAll('.profile-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.profile-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.profile-pane').forEach(p => p.classList.remove('active'));
      const pane = document.getElementById(btn.dataset.pane);
      if (pane) pane.classList.add('active');
    });
  });

  // ---- Year bars (profile · indicadores) ----
  const yb = document.getElementById('year-bars');
  if (yb) {
    const data = [
      {y:'2017', v:11}, {y:'2018', v:14}, {y:'2019', v:13}, {y:'2020', v:16},
      {y:'2021', v:17}, {y:'2022', v:18}, {y:'2023', v:19}, {y:'2024', v:21},
      {y:'2025', v:8},  {y:'2026', v:5}
    ];
    const max = Math.max(...data.map(d => d.v));
    yb.innerHTML = data.map(d => `
      <div class="year-bar" title="${d.y}: ${d.v} produções">
        <div class="year-bar-track" style="height:${(d.v/max)*100}px;">
          <span class="year-bar-val">${d.v}</span>
        </div>
        <div class="year-bar-label">${d.y.slice(2)}</div>
      </div>
    `).join('');
  }

  // ---- Hash routing ----
  function applyHashRoute() {
    const hash = window.location.hash.replace('#','');
    if (screens.includes(hash)) {
      showScreen(hash);
    } else {
      setTopbar('busca');
    }
  }
  window.addEventListener('hashchange', applyHashRoute);
  applyHashRoute();

  if (window.lucide) lucide.createIcons();
})();
