(() => {
  'use strict';
  const themeKey = 'aurora_theme_v1';
  const shortcutsKey = 'aurora_shortcuts_v1';
  const themes = [
    { id: 'aurora', name: 'Aurora', colors: ['#07111f', '#55d8e7', '#347cff'] },
    { id: 'violet', name: 'Violeta', colors: ['#100e1b', '#c09aff', '#7e68ea'] },
    { id: 'amber', name: 'Âmbar', colors: ['#15130f', '#f2b85b', '#d88044'] },
    { id: 'forest', name: 'Bosque', colors: ['#071611', '#66e0a0', '#2caa83'] },
    { id: 'ice', name: 'Gelo', colors: ['#eaf2f7', '#087eaa', '#4266ca'] }
  ];
  const coreItems = [
    ['dashboard', '⌂', 'Dashboard', '/'],
    ['printer', '▣', 'Impressora 3D', '/#printer-card'],
    ['camera', '◉', 'Câmera', '/#camera-card'],
    ['system', '⚙', 'Sistema', '/#system-card'],
    ['network', '⌁', 'Rede', '/network.html'],
    ['services', '✣', 'Serviços', '/#services-card'],
    ['storage', '▤', 'Armazenamento', '/#storage-card'],
    ['history', '◴', 'Histórico', '/history.html'],
    ['backup', '☁', 'Backup', '/#backup-card'],
    ['diagnostics', '✥', 'Diagnóstico', '/diagnostics.html'],
    ['homeboard', '◆', 'HomeBoard', '/homeboard'],
    ['homeassistant', '⌂', 'Home Assistant', '/homeassistant'],
    ['opengym', '💪', 'openGym', '/opengym'],
    ['manyfold', '🧊', 'Manyfold', '/manyfold'],
    ['mealie', '🍽️', 'Mealie', '/mealie'],
    ['actual', '💰', 'Actual Budget', '/actual']
  ].map(([id, icon, label, href]) => ({ id, icon, label, href }));

  function read(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch (_) { return fallback; } }
  function save(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) { /* Preferências opcionais. */ } }
  function getPrimary() {
    const chosen = read(shortcutsKey, ['dashboard', 'opengym', 'services']);
    const valid = Array.isArray(chosen) ? [...new Set(chosen)].filter(id => coreItems.some(item => item.id === id)) : [];
    return valid.length === 3 ? valid : ['dashboard', 'opengym', 'services'];
  }
  function currentId() {
    const path = location.pathname.replace(/\/$/, '') || '/';
    if (path.endsWith('/fitness-exercicios.html')) return 'exercises';
    if (path.endsWith('/fitness-planos.html')) return 'plans';
    if (path.endsWith('/fitness.html')) return 'fitness';
    if (path.endsWith('/network.html')) return 'network';
    if (path.endsWith('/history.html')) return 'history';
    if (path.endsWith('/diagnostics.html')) return 'diagnostics';
    if (location.hash.includes('printer')) return 'printer';
    if (location.hash.includes('camera')) return 'camera';
    if (location.hash.includes('services')) return 'services';
    if (location.hash.includes('storage')) return 'storage';
    if (location.hash.includes('backup')) return 'backup';
    if (location.hash.includes('system')) return 'system';
    return 'dashboard';
  }
  function makeAnchor(item, more = false) {
    const anchor = document.createElement('a');
    anchor.href = item.href;
    anchor.className = more ? 'aurora-more-link' : 'aurora-shortcut';
    anchor.dataset.itemId = item.id;
    anchor.setAttribute('aria-label', item.label);
    anchor.title = item.label;
    anchor.innerHTML = `<span aria-hidden="true">${item.icon}</span><span class="aurora-link-label">${item.label}</span>`;
    return anchor;
  }
  const sidebar = document.querySelector('.sidebar') || (() => {
    const node = document.createElement('aside');
    node.className = 'sidebar aurora-generated-sidebar';
    node.innerHTML = '<div class="logo"><span class="logo-mark">✦</span></div><nav class="side-nav"></nav><div class="side-foot"></div>';
    document.body.prepend(node);
    document.body.classList.add('aurora-generated-shell');
    return node;
  })();
  sidebar.classList.add('aurora-compact-sidebar');
  document.body.classList.add('aurora-has-compact-nav');
  let nav = sidebar.querySelector('.side-nav');
  if (!nav) { nav = document.createElement('nav'); nav.className = 'side-nav'; sidebar.append(nav); }
  nav.replaceChildren();

  const primaryNav = document.createElement('div'); primaryNav.className = 'aurora-primary-nav';
  const moreButton = document.createElement('button'); moreButton.type = 'button'; moreButton.className = 'aurora-more-toggle'; moreButton.innerHTML = '<span aria-hidden="true">•••</span><span class="aurora-link-label">Mais</span>'; moreButton.setAttribute('aria-label', 'Mais páginas e configurações'); moreButton.title = 'Mais'; moreButton.setAttribute('aria-expanded', 'false');
  nav.append(primaryNav, moreButton);
  const panel = document.createElement('section'); panel.className = 'aurora-more-panel'; panel.hidden = true; panel.setAttribute('aria-label', 'Mais páginas e configurações');
  const panelHead = document.createElement('div'); panelHead.className = 'aurora-menu-head'; panelHead.innerHTML = '<span class="aurora-mark">✦</span><button type="button" class="aurora-close" aria-label="Fechar menu">×</button>';
  const moreLinks = document.createElement('nav'); moreLinks.className = 'aurora-more-links'; moreLinks.setAttribute('aria-label', 'Outras páginas');
  const sectionTitle = document.createElement('h2'); sectionTitle.className = 'aurora-setting-title'; sectionTitle.textContent = 'Esquema de cores';
  const palette = document.createElement('div'); palette.className = 'aurora-palette';
  themes.forEach(theme => { const button = document.createElement('button'); button.type = 'button'; button.className = 'aurora-theme-choice'; button.dataset.theme = theme.id; button.setAttribute('aria-label', `Usar esquema ${theme.name}`); button.innerHTML = `<span class="aurora-swatches">${theme.colors.map(color => `<i style="--swatch:${color}"></i>`).join('')}</span><span>${theme.name}</span>`; palette.append(button); });
  const customize = document.createElement('button'); customize.type = 'button'; customize.className = 'aurora-customize'; customize.innerHTML = '<span aria-hidden="true">⚙</span> Personalizar atalhos';
  panel.append(panelHead, moreLinks, sectionTitle, palette, customize); document.body.append(panel);

  const dialog = document.createElement('dialog'); dialog.className = 'aurora-shortcuts-dialog';
  dialog.innerHTML = '<form method="dialog"><div class="aurora-dialog-head"><h2>Atalhos principais</h2><button class="aurora-close" aria-label="Fechar">×</button></div><p>Escolha três páginas para o menu compacto.</p><div class="aurora-checks"></div><div class="aurora-dialog-actions"><button value="cancel" class="aurora-cancel">Cancelar</button><button value="save" class="aurora-save">Salvar atalhos</button></div></form>';
  document.body.append(dialog);
  const checks = dialog.querySelector('.aurora-checks');
  coreItems.forEach(item => { const label = document.createElement('label'); label.className = 'aurora-check'; label.innerHTML = `<input type="checkbox" value="${item.id}"><span aria-hidden="true">${item.icon}</span><span>${item.label}</span>`; checks.append(label); });

  function renderNav() {
    const primary = getPrimary(), active = currentId();
    primaryNav.replaceChildren(); moreLinks.replaceChildren();
    primary.forEach(id => { const item = coreItems.find(entry => entry.id === id); const anchor = makeAnchor(item); if (item.id === active) { anchor.classList.add('active'); anchor.setAttribute('aria-current', 'page'); } primaryNav.append(anchor); });
    const rest = coreItems.filter(item => !primary.includes(item.id));
    const moreIsCurrent = rest.some(item => item.id === active);
    moreButton.classList.toggle('active', moreIsCurrent);
    if (moreIsCurrent) moreButton.setAttribute('aria-current', 'page'); else moreButton.removeAttribute('aria-current');
    rest.forEach(item => { const anchor = makeAnchor(item, true); if (item.id === active) { anchor.classList.add('active'); anchor.setAttribute('aria-current', 'page'); } moreLinks.append(anchor); });
    document.querySelectorAll('.aurora-theme-choice').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.theme === (document.documentElement.dataset.auroraTheme || 'aurora'))));
  }
  function setTheme(theme) {
    if (!themes.some(item => item.id === theme)) theme = 'aurora';
    document.documentElement.dataset.auroraTheme = theme;
    save(themeKey, theme);
    document.querySelectorAll('.aurora-theme-choice').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.theme === theme)));
    document.dispatchEvent(new CustomEvent('aurora:themechange', { detail: { theme } }));
  }
  function closeMore() { panel.hidden = true; moreButton.setAttribute('aria-expanded', 'false'); }
  moreButton.addEventListener('click', () => { panel.hidden = !panel.hidden; moreButton.setAttribute('aria-expanded', String(!panel.hidden)); });
  panelHead.querySelector('.aurora-close').addEventListener('click', closeMore);
  document.addEventListener('click', event => { if (!panel.hidden && !panel.contains(event.target) && !moreButton.contains(event.target)) closeMore(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMore(); });
  panel.addEventListener('click', event => { if (event.target.closest('a')) closeMore(); });
  palette.addEventListener('click', event => { const button = event.target.closest('[data-theme]'); if (button) setTheme(button.dataset.theme); });
  customize.addEventListener('click', () => { closeMore(); const primary = getPrimary(); checks.querySelectorAll('input').forEach(input => { input.checked = primary.includes(input.value); }); dialog.showModal(); });
  checks.addEventListener('change', event => { const selected = [...checks.querySelectorAll('input:checked')]; if (selected.length > 3) event.target.checked = false; });
  dialog.querySelector('form').addEventListener('submit', event => {
    const submitter = event.submitter;
    if (submitter?.value !== 'save') return;
    event.preventDefault(); const selected = [...checks.querySelectorAll('input:checked')].map(input => input.value);
    if (selected.length !== 3) { dialog.querySelector('p').textContent = 'Selecione exatamente três páginas.'; return; }
    save(shortcutsKey, selected); dialog.close(); renderNav();
  });
  document.querySelectorAll('.aurora-close').forEach(button => { if (button.closest('dialog')) button.addEventListener('click', event => { event.preventDefault(); dialog.close(); }); });
  document.addEventListener('click', event => { const link = event.target.closest('.aurora-shortcut,.aurora-more-link'); if (link) { closeMore(); } });
  window.addEventListener('hashchange', renderNav); window.addEventListener('popstate', renderNav);
  setTheme(read(themeKey, document.documentElement.dataset.auroraTheme || 'aurora'));
  renderNav();
})();
