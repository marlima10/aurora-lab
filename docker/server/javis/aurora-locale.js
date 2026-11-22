// Migrate existing browsers once; subsequent explicit language choices remain native.
(() => {
  try {
    if (localStorage.getItem('aurora.locale.version') !== '36') {
      localStorage.setItem('javis.ui_lang', 'pt');
      localStorage.setItem('javis.voice', 'pt-BR-FranciscaNeural');
      localStorage.setItem('aurora.locale.version', '36');
    }
  } catch (_) { /* Native server preference still supplies the language. */ }
})();
