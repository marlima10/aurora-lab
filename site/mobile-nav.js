(() => {
  const button = document.getElementById('menuToggle');
  const sidebar = document.querySelector('.sidebar');
  const scrim = document.getElementById('navScrim');
  if (!button || !sidebar || !scrim) return;

  const closeMenu = () => {
    sidebar.classList.remove('is-open');
    document.body.classList.remove('nav-open');
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-label', 'Abrir menu');
    scrim.hidden = true;
  };

  button.addEventListener('click', () => {
    const opening = !sidebar.classList.contains('is-open');
    sidebar.classList.toggle('is-open', opening);
    document.body.classList.toggle('nav-open', opening);
    button.setAttribute('aria-expanded', String(opening));
    button.setAttribute('aria-label', opening ? 'Fechar menu' : 'Abrir menu');
    scrim.hidden = !opening;
  });
  scrim.addEventListener('click', closeMenu);
  sidebar.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeMenu();
  });
  window.addEventListener('resize', () => {
    if (window.innerWidth > 850) closeMenu();
  });
})();
