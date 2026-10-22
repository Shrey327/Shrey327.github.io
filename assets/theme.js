/* Apply the preference before CSS paints. No requests or tracking. */
(() => {
  const root = document.documentElement;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  let choice;
  try { choice = localStorage.getItem('blog-theme'); } catch {}
  if (choice !== 'dark' && choice !== 'light') choice = null;
  let button;
  function apply() {
    const dark = choice ? choice === 'dark' : system.matches;
    root.dataset.theme = dark ? 'dark' : 'light';
    if (button) button.setAttribute('aria-pressed', String(dark));
  }
  apply();
  system.addEventListener('change', () => { if (!choice) apply(); });
  document.addEventListener('DOMContentLoaded', () => {
    button = document.querySelector('[data-theme-toggle]');
    if (!button) return;
    button.hidden = false;
    apply();
    button.addEventListener('click', () => {
      choice = root.dataset.theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem('blog-theme', choice); } catch {}
      apply();
    });
  });
})();
