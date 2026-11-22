// Migrate existing browsers once; subsequent explicit language choices remain native.
(() => {
  try {
    if (localStorage.getItem('aurora.locale.version') !== '36') {
      localStorage.setItem('javis.ui_lang', 'pt');
      localStorage.setItem('javis.voice', 'pt-BR-FranciscaNeural');
      localStorage.setItem('aurora.locale.version', '36');
    }
    if (localStorage.getItem('aurora.voice.profile.version') !== '38') {
      localStorage.setItem('javis.voice', 'pt-BR-AntonioNeural');
      localStorage.setItem('javis.rate', '0.90');
      localStorage.setItem('aurora.voice.profile.version', '38');
    }
  } catch (_) { /* Native server preference still supplies the language. */ }
})();
